import json
from pathlib import Path
from typing import Dict, Any, Optional

# tensorflowはインストールされていても、型チェッカーがstubを見つけられないことがあるため無視します
import tensorflow as tf  

from sionna.rt import load_scene, RadioMaterial, Transmitter, Receiver, PlanarArray, Scene

class SionnaSimulator:
    """生成されたシーンXMLとマニフェストを読み込み、電波シミュレーションを実行するクラス"""

    def __init__(self, xml_path: Path, manifest_path: Path):
        self.xml_path = xml_path
        self.manifest_path = manifest_path
        # 型ヒントを明記 (None または Scene)
        self.scene: Optional[Scene] = None

    def run_coverage_simulation(self, output_dir: Path) -> Path:
        """
        シーンをロードしてマテリアルを適用し、カバレッジマップ（電波到達範囲）を計算・保存する
        """
        print("--- Starting Sionna-RT Simulation ---")
        
        # 1. シーンのロード
        print(f"Loading scene from {self.xml_path}...")
        self.scene = load_scene(str(self.xml_path))
        # 型チェッカーに self.scene が None ではないことを保証させる
        assert self.scene is not None, "Failed to load Sionna scene."

        # 2. マニフェストの読み込みとマテリアルの動的アサイン
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        self._assign_materials(manifest.get("material_mapping", {}))

        # 3. アンテナと送受信機 (Tx/Rx) のセットアップ
        self._setup_transceivers(manifest.get("center_lat_lon", [0, 0]))

        # 4. カバレッジマップの計算 (レイトレーシング実行)
        print("Computing coverage map...")
        # 修正: compute_coverage_map -> coverage_map (引数の型警告も無視してPythonのリストを渡す)
        cm = self.scene.coverage_map(
            cm_center=[0, 0, 1.5],
            cm_orientation=[0, 0, 0],
            cm_size=[200, 200],
            cm_res=[1, 1],
            max_depth=3
        )

        # 5. 計算結果の保存
        cm_output_path = output_dir / f"{self.xml_path.stem}_coverage.npy"
        
        import numpy as np
        # as_tensor().numpy() でTensorFlowからNumPy配列に変換
        np.save(cm_output_path, cm.as_tensor().numpy())
        print(f"Coverage map saved to {cm_output_path}")

        return cm_output_path

    def _assign_materials(self, material_mapping: Dict[str, str]) -> None:
        """マニフェストの辞書に基づき、オブジェクトごとにRadioMaterialを適用する"""
        assert self.scene is not None
        
        loaded_materials: Dict[str, RadioMaterial] = {}

        for object_id, itu_name in material_mapping.items():
            obj = self.scene.get(object_id)
            if obj is None:
                print(f"Warning: Object '{object_id}' not found in scene.")
                continue

            if itu_name not in loaded_materials:
                loaded_materials[itu_name] = RadioMaterial(itu_name)

            # 修正: scene.get() の戻り値の型定義が曖昧なため、型チェッカーを無視して上書き
            obj.radio_material = loaded_materials[itu_name]
        
        print(f"Assigned materials to {len(material_mapping)} objects.")

    def _setup_transceivers(self, center_lat_lon: list) -> None:
        """送受信機の初期配置"""
        assert self.scene is not None

        self.scene.tx_array = PlanarArray(
            num_rows=4, num_cols=4, vertical_spacing=0.5, horizontal_spacing=0.5, 
            pattern="tr38901", polarization="V"
        )
        
        self.scene.rx_array = PlanarArray(
            num_rows=1, num_cols=1, vertical_spacing=0.5, horizontal_spacing=0.5, 
            pattern="dipole", polarization="V"
        )

        # 修正: 実体はリストを受け付けるが、型stubがmitsuba.Point3fを要求するため無視
        tx = Transmitter(name="tx_base_station", position=[-50, -50, 30.0])
        self.scene.add(tx)
        
        self.scene.frequency = 3.5e9