import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List

from plateau_rt.domain.models import Scene as DomainScene, MaterialType
from plateau_rt.adapters.geometry.trimesh_adapter import MeshRecord


class SionnaSceneCompiler:
    """ドメインのシーン情報と生成済みメッシュ情報をSionna-RT用のMitsuba XMLにコンパイルするクラス"""

    # ドメインのマテリアルをSionna(ITU)のプリセット名にマッピング
    # （XMLには書き込まず、後のSionna-RT実行フェーズでPython側からアサインする際に利用します）
    MATERIAL_MAP = {
        MaterialType.CONCRETE: "itu_concrete",
        MaterialType.WOOD: "itu_wood",
        MaterialType.GLASS: "itu_glass",
        MaterialType.METAL: "itu_metal",
        MaterialType.DEFAULT: "itu_concrete",
    }

    def compile(
        self, domain_scene: DomainScene, mesh_records: List[MeshRecord], output_dir: Path
    ) -> Path:
        """
        PLYファイル群を参照するMitsuba XMLを生成し、保存する。
        """
        xml_path = output_dir / f"{domain_scene.scene_id}.xml"
        self._write_mitsuba_xml(mesh_records, xml_path)
        print(f"Sionna scene compiled at {xml_path}")
        return xml_path

    def _write_mitsuba_xml(self, mesh_records: List[MeshRecord], out_path: Path) -> None:
        """内部処理: XMLツリーを構築して整形保存する"""

        # ルート要素 (Mitsuba 3の仕様に基づく)
        scene_el = ET.Element("scene", version="3.0.0")

        # 1. プレースホルダー用マテリアルの定義
        # Sionna-RTのパースエラーを回避するため、標準の「diffuse」を一つ定義しておく
        bsdf_el = ET.SubElement(scene_el, "bsdf", type="diffuse", id="dummy_material")
        ET.SubElement(bsdf_el, "rgb", name="reflectance", value="0.5, 0.5, 0.5")

        # 2. メッシュ (PLY) の参照追加
        for record in mesh_records:
            # XMLファイルから見たPLYファイルへの相対パス（同じディレクトリに出力されている前提）
            rel_path = record.file_path.name

            # <shape type="ply" id="bldg_001_roof">
            shape_el = ET.SubElement(scene_el, "shape", type="ply", id=record.object_id)

            #   <string name="filename" value="bldg_001_roof.ply"/>
            ET.SubElement(shape_el, "string", name="filename", value=rel_path)

            #   <ref id="dummy_material" name="bsdf"/>
            ET.SubElement(shape_el, "ref", id="dummy_material", name="bsdf")

        # 3. XMLの整形 (pretty print) と保存
        xml_str = ET.tostring(scene_el, encoding="utf-8")
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml = parsed_xml.toprettyxml(indent="    ")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
