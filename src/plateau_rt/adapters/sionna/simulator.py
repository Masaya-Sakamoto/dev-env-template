import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# tfの代わりにSionna 1.0のRadioMapSolverをインポート
from sionna.rt import load_scene, Transmitter, Receiver, PlanarArray, Scene, RadioMapSolver

class SionnaSimulator:
    def __init__(self, xml_path: Path, manifest_path: Path):
        self.xml_path = xml_path
        self.manifest_path = manifest_path
        self.scene: Optional[Scene] = None

    def run_coverage_simulation(self, output_dir: Path) -> Path:
        print("--- Starting Sionna-RT Simulation ---")
        
        # 1. シーンのロード
        print(f"Loading scene from {self.xml_path}...")
        self.scene = load_scene(str(self.xml_path))
        assert self.scene is not None, "Failed to load Sionna scene."

        # 2. マニフェストの読み込み
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        # 3. アンテナと送受信機 (Tx/Rx) のセットアップ
        self._setup_transceivers(manifest.get("center_lat_lon", [0, 0]))

        # 4. カバレッジマップの計算 (Sionna 1.0以降のRadioMapSolverを使用)
        print("Computing coverage map...")
        rm_solver = RadioMapSolver()
        rm = rm_solver(
            self.scene,
            max_depth=3,
            cell_size=[1.0, 1.0],
            center=[0.0, 0.0, 1.5],
            size=[200.0, 200.0],
            orientation=[0.0, 0.0, 0.0]
        ) # type: ignore

        # 5. 計算結果の保存
        cm_output_path = output_dir / f"{self.xml_path.stem}_coverage.npy"
        
        # Sionna 1.0ではDr.Jitテンソルが返るため、np.array() でNumpy配列にキャストして保存
        np.save(cm_output_path, np.array(rm.path_gain))
        print(f"Coverage map saved to {cm_output_path}")

        return cm_output_path

    def _setup_transceivers(self, center_lat_lon: list) -> None:
        assert self.scene is not None

        self.scene.tx_array = PlanarArray(
            num_rows=4, num_cols=4, vertical_spacing=0.5, horizontal_spacing=0.5, 
            pattern="tr38901", polarization="V"
        )
        self.scene.rx_array = PlanarArray(
            num_rows=1, num_cols=1, vertical_spacing=0.5, horizontal_spacing=0.5, 
            pattern="dipole", polarization="V"
        )

        tx = Transmitter(name="tx_base_station", position=[-50, -50, 30.0])  # type: ignore
        self.scene.add(tx)
        
        self.scene.frequency = 3.5e9