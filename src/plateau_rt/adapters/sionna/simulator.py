import json
from pathlib import Path
from typing import Dict, Any

# Sionna-RTのコア機能（ここで初めてCUDA・GPU依存の重い処理がロードされます）
from sionna.rt import load_scene, RadioMaterial, Transmitter, Receiver, PlanarArray
import tensorflow as tf  # Sionnaのバックエンド計算用

class SionnaSimulator:
    """生成されたシーンXMLとマニフェストを読み込み、電波シミュレーションを実行するクラス"""

    def __init__(self, xml_path: Path, manifest_path: Path):
        self.xml_path = xml_path
        self.manifest_path = manifest_path
        self.scene = None

    def run_coverage_simulation(self, output_dir: Path) -> Path:
        """
        シーンをロードしてマテリアルを適用し、カバレッジマップ（電波到達範囲）を計算・保存する
        """
        print("--- Starting Sionna-RT Simulation ---")
        
        # 1. シーンのロード (この時点ではすべてダミーのdiffuseマテリアル)
        print(f"Loading scene from {self.xml_path}...")
        self.scene = load_scene(str(self.xml_path))

        # 2. マニフェストの読み込みとマテリアルの動的アサイン
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        self._assign_materials(manifest.get("material_mapping", {}))

        # 3. アンテナと送受信機 (Tx/Rx) のセットアップ
        self._setup_transceivers(manifest.get("center_lat_lon", [0, 0]))

        # 4. カバレッジマップの計算 (レイトレーシング実行)
        print("Computing coverage map...")
        # 例: 基地局を中心に 200m x 200m の範囲を 1m メッシュで計算
        cm = self.scene.compute_coverage_map(
            cm_center=[0, 0, 1.5], # ローカル座標の原点付近、高さ1.5m
            cm_orientation=[0, 0, 0],
            cm_size=[200, 200],
            cm_res=[1, 1],
            max_depth=3 # 反射・回折の最大回数
        )

        # 5. 計算結果の保存 (.npy 等でデータセットとして保存)
        cm_output_path = output_dir / f"{self.xml_path.stem}_coverage.npy"
        
        # Numpy配列として保存 (TensorFlowのTensorをnumpyに変換)
        import numpy as np
        np.save(cm_output_path, cm.as_tensor().numpy())
        print(f"Coverage map saved to {cm_output_path}")

        return cm_output_path

    def _assign_materials(self, material_mapping: Dict[str, str]) -> None:
        """マニフェストの辞書に基づき、オブジェクトごとにRadioMaterialを適用する"""
        
        # マテリアルインスタンスのキャッシュ（同じプリセットを何度もロードしないため）
        loaded_materials: Dict[str, RadioMaterial] = {}

        for object_id, itu_name in material_mapping.items():
            # Sionnaシーン内から対象のオブジェクト(PLYメッシュ)を検索
            obj = self.scene.get(object_id)
            if obj is None:
                print(f"Warning: Object '{object_id}' not found in scene.")
                continue

            # キャッシュになければ新規インスタンス化
            if itu_name not in loaded_materials:
                loaded_materials[itu_name] = RadioMaterial(itu_name)

            # Python API経由でマテリアルを上書き（バグ回避の要）
            obj.radio_material = loaded_materials[itu_name]
        
        print(f"Assigned materials to {len(material_mapping)} objects.")

    def _setup_transceivers(self, center_lat_lon: list) -> None:
        """送受信機の初期配置 (データセット要件に合わせてパラメータ化可能)"""
        # 送信アンテナ(基地局): 3GPP TR38.901モデル
        self.scene.tx_array = PlanarArray(
            num_rows=4, num_cols=4, vertical_spacing=0.5, horizontal_spacing=0.5, 
            pattern="tr38901", polarization="V"
        )
        
        # 受信アンテナ(端末): 無指向性ダイポール
        self.scene.rx_array = PlanarArray(
            num_rows=1, num_cols=1, vertical_spacing=0.5, horizontal_spacing=0.5, 
            pattern="dipole", polarization="V"
        )

        # 基地局の配置 (例: ローカル原点から少し離れた高さ30mの場所)
        tx = Transmitter(name="tx_base_station", position=[-50, -50, 30.0])
        self.scene.add(tx)
        
        # 端末はカバレッジマップ計算では不要ですが、パス(Ray)を可視化・計算するならRxが必要です
        # rx = Receiver(name="rx_user_equipment", position=[10, 10, 1.5])
        # self.scene.add(rx)
        
        # 周波数の設定 (例: 3.5GHz)
        self.scene.frequency = 3.5e9