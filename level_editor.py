import copy
import math
import os
import sys
import bpy
import bpy_extras
import gpu
import gpu_extras.batch
import mathutils

# Windows環境でのコンソール文字コードを UTF-8 (CP65001) に設定
if sys.platform == "win32":
    try:
        os.system("chcp 65001 > nul")
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ブレンダーに登録するアドオン情報
bl_info = {
    "name": "レベルエディタ",
    "author": "Taro Kamata",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "location": "",
    "description": "レベルエディタ",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"
}

# アドオン有効化時コールバック
def register():
    # Blenderにクラスを登録
    for cls in classes:
        bpy.utils.register_class(cls)

    # メニュー項目を追加
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)
    # 3Dビューに描画関数を追加
    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(
        DrawCollider.draw_collider, (), "WINDOW", "POST_VIEW"
    )
    print("レベルエディタが有効化されました。")
    
# アドオン無効化時コールバック
def unregister():
    # メニュー項目を削除
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)
    # 3Dビューから描画関数を削除
    if DrawCollider.handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(DrawCollider.handle, "WINDOW")
        DrawCollider.handle = None

    # Blenderからクラスを削除
    for cls in classes:
        bpy.utils.unregister_class(cls)
    print("レベルエディタが無効化されました。")
    
# メニュー項目描画
def draw_menu_manual(self, context):
    self.layout.operator("wm.url_open_preset", text="Manual", icon='HELP')

# オペレータ 頂点を伸ばす
class MYADDON_OT_stretch_vertex(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_stretch_vertex"
    bl_label = "頂点を伸ばす"
    bl_description = "頂点座標を引っ張って伸ばします"
    # リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0
        print("頂点を伸ばしました。")

        # オペレータの命令終了を通知
        return {'FINISHED'}

# オペレータ ICO球生成
class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_create_object"
    bl_label = "ICO球生成"
    bl_description = "ICO球を生成します"
    # リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれる関数
    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add()
        print("ICO球を生成しました。")

        return {'FINISHED'}

# オペレータ シーン出力
class MYADDON_OT_export_scene(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "myaddon.myaddon_ot_export_scene"
    bl_label = "シーン出力"
    bl_description = "シーン情報をExportします"

    # 出力するファイルの拡張子
    filename_ext = ".scene"

    def write_and_print(self, file, str):
        """コンソール表示とファイル書き出しを同時におこなう"""
        newline_character = "\n"
        print(str)
        file.write(str)
        file.write(newline_character)

    def parse_scene_recursive(self, file, object, level):
        """シーン解析用再帰関数"""
        # マジックナンバー・文字列の定数定義
        tab_indent = "\t"
        empty_str = ""
        property_filename = "file_name"
        property_collider = "collider"
        property_collider_center = "collider_center"
        property_collider_size = "collider_size"
        fmt_trans = "T %f %f %f"
        fmt_rot = "R %f %f %f"
        fmt_scale = "S %f %f %f"
        fmt_filename = "N %s"
        fmt_collider = "C %s"
        fmt_collider_center = "CC %f %f %f"
        fmt_collider_size = "CS %f %f %f"
        tag_end = "END"

        # 深さ分インデントする (タブを挿入)
        indent = empty_str
        for i in range(level):
            indent += tab_indent

        # オブジェクト種別書き込み
        self.write_and_print(file, indent + object.type)

        # ローカルトランスフォーム行列から平行移動、回転、スケーリングを抽出
        trans, rot, scale = object.matrix_local.decompose()

        # 回転を Quaternion から Euler (3軸での回転角) に変換
        rot = rot.to_euler()

        # ラジアンから度数法に変換
        rot.x = math.degrees(rot.x)
        rot.y = math.degrees(rot.y)
        rot.z = math.degrees(rot.z)

        # トランスフォーム情報を表示
        self.write_and_print(file, indent + fmt_trans % (trans.x, trans.y, trans.z))
        self.write_and_print(file, indent + fmt_rot % (rot.x, rot.y, rot.z))
        self.write_and_print(file, indent + fmt_scale % (scale.x, scale.y, scale.z))

        # カスタムプロパティ 'file_name' の出力
        if property_filename in object:
            self.write_and_print(file, indent + fmt_filename % object[property_filename])

        # カスタムプロパティ 'collider' の出力
        if property_collider in object:
            self.write_and_print(file, indent + fmt_collider % object[property_collider])
            if property_collider_center in object:
                center = object[property_collider_center]
                self.write_and_print(file, indent + fmt_collider_center % (center[0], center[1], center[2]))
            if property_collider_size in object:
                size = object[property_collider_size]
                self.write_and_print(file, indent + fmt_collider_size % (size[0], size[1], size[2]))

        self.write_and_print(file, indent + tag_end)
        self.write_and_print(file, empty_str)

        # 子ノードへ進む(深さが1上がる)
        next_level_increment = 1
        for child in object.children:
            self.parse_scene_recursive(file, child, level + next_level_increment)

    def export(self):
        """ファイルに出力"""
        print("シーン情報出力開始... %r" % self.filepath)

        with open(self.filepath, "wt") as file:
            self.write_and_print(file, "SCENE")

            # シーン直下のオブジェクトをルートノード(深さ0)とし、再帰関数で走査
            initial_depth = 0
            for object in bpy.context.scene.objects:
                # 親オブジェクトがあるものはスキップ (代わりに親から呼び出すから)
                if object.parent:
                    continue

                self.parse_scene_recursive(file, object, initial_depth)

    # メニューを実行したときに呼ばれる関数
    def execute(self, context):
        print("シーン情報をExportします")

        # ファイルに出力
        self.export()

        print("シーン情報をExportしました")
        self.report({'INFO'}, "シーン情報をExportしました")

        return {'FINISHED'}

# オペレータ カスタムプロパティ['file_name']追加
class MYADDON_OT_add_filename(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_filename"
    bl_label = "FileName 追加"
    bl_description = "['file_name']カスタムプロパティを追加します"
    # リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        property_name = "file_name"
        initial_value = ""
        # ['file_name']カスタムプロパティを追加
        context.object[property_name] = initial_value

        return {'FINISHED'}

# パネル ファイル名
class OBJECT_PT_file_name(bpy.types.Panel):
    """オブジェクトのファイルネームパネル"""
    bl_idname = "OBJECT_PT_file_name"
    bl_label = "FileName"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    # サブメニューの描画
    def draw(self, context):
        property_name = "file_name"
        prop_path = '["file_name"]'

        # パネルに項目を追加
        if property_name in context.object:
            # 既にプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, prop_path, text=self.bl_label)
        else:
            # プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_add_filename.bl_idname)

# オペレータ カスタムプロパティ['collider']追加
class MYADDON_OT_add_collider(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_collider"
    bl_label = "コライダー 追加"
    bl_description = "['collider']カスタムプロパティを追加します"
    # リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        prop_collider = "collider"
        prop_center = "collider_center"
        prop_size = "collider_size"

        default_type = "BOX"
        default_center = mathutils.Vector((0.0, 0.0, 0.0))
        default_size = mathutils.Vector((2.0, 2.0, 2.0))

        # ['collider']カスタムプロパティを追加
        context.object[prop_collider] = default_type
        context.object[prop_center] = default_center
        context.object[prop_size] = default_size

        return {'FINISHED'}

# パネル コライダー
class OBJECT_PT_collider(bpy.types.Panel):
    """オブジェクトのコライダーパネル"""
    bl_idname = "OBJECT_PT_collider"
    bl_label = "Collider"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    # サブメニューの描画
    def draw(self, context):
        prop_collider = "collider"
        prop_center = "collider_center"
        prop_size = "collider_size"

        # パネルに項目を追加
        if prop_collider in context.object:
            # 既にプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, '["' + prop_collider + '"]', text="Type")
            self.layout.prop(context.object, '["' + prop_center + '"]', text="Center")
            self.layout.prop(context.object, '["' + prop_size + '"]', text="Size")
        else:
            # プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_add_collider.bl_idname)

# コライダー描画
class DrawCollider:
    # 描画ハンドル
    handle = None

    # 3Dビューに登録する描画関数
    @staticmethod
    def draw_collider():
        # 定数定義 (マジックナンバー回避)
        prop_collider = "collider"
        prop_center = "collider_center"
        prop_size = "collider_size"

        default_center_val = (0.0, 0.0, 0.0)
        default_size_val = (2.0, 2.0, 2.0)
        offset_val = 0.5

        offsets = [
            [-offset_val, -offset_val, -offset_val],  # 左下前
            [+offset_val, -offset_val, -offset_val],  # 右下前
            [-offset_val, +offset_val, -offset_val],  # 左上前
            [+offset_val, +offset_val, -offset_val],  # 右上前
            [-offset_val, -offset_val, +offset_val],  # 左下奥
            [+offset_val, -offset_val, +offset_val],  # 右下奥
            [-offset_val, +offset_val, +offset_val],  # 左上奥
            [+offset_val, +offset_val, +offset_val],  # 右上奥
        ]
        draw_color = [0.5, 1.0, 1.0, 1.0]

        # 頂点データ・インデックスデータ
        vertices = {"pos": []}
        indices = []

        # シーン内のオブジェクトを走査
        for obj in bpy.context.scene.objects:
            # コライダープロパティがなければ、描画をスキップ
            if prop_collider not in obj:
                continue

            # 中心点、サイズの変数を宣言
            center = mathutils.Vector(default_center_val)
            size = mathutils.Vector(default_size_val)

            # プロパティから値を抽出
            if prop_center in obj:
                center[0] = obj[prop_center][0]
                center[1] = obj[prop_center][1]
                center[2] = obj[prop_center][2]

            if prop_size in obj:
                size[0] = obj[prop_size][0]
                size[1] = obj[prop_size][1]
                size[2] = obj[prop_size][2]

            # 追加前の頂点数
            start_idx = len(vertices["pos"])

            # Boxの8頂点分回す
            for offset in offsets:
                # オブジェクトの中心座標をコピー
                pos = copy.copy(center)
                # 中心点を基準に各頂点ごとにずらす
                pos[0] += offset[0] * size[0]
                pos[1] += offset[1] * size[1]
                pos[2] += offset[2] * size[2]
                # ローカル座標からワールド座標に変換
                pos = obj.matrix_world @ pos
                # 頂点データリストに座標を追加
                vertices["pos"].append(pos)

            # 前面を構成する辺の頂点インデックス
            indices.append([start_idx + 0, start_idx + 1])
            indices.append([start_idx + 2, start_idx + 3])
            indices.append([start_idx + 0, start_idx + 2])
            indices.append([start_idx + 1, start_idx + 3])
            # 奥面を構成する辺の頂点インデックス
            indices.append([start_idx + 4, start_idx + 5])
            indices.append([start_idx + 6, start_idx + 7])
            indices.append([start_idx + 4, start_idx + 6])
            indices.append([start_idx + 5, start_idx + 7])
            # 手前と奥を繋ぐ辺の頂点インデックス
            indices.append([start_idx + 0, start_idx + 4])
            indices.append([start_idx + 1, start_idx + 5])
            indices.append([start_idx + 2, start_idx + 6])
            indices.append([start_idx + 3, start_idx + 7])

        # 描画対象の頂点が無い場合は処理をスキップ
        if len(vertices["pos"]) == 0:
            return

        # ビルトインのシェーダを取得
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")

        # バッチを作成
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", vertices, indices=indices)

        # シェーダのパラメータ設定と描画
        shader.bind()
        shader.uniform_float("color", draw_color)
        batch.draw(shader)


# トップバーの拡張メニュー
class TOPBAR_MT_my_menu(bpy.types.Menu):
    # Blenderがクラスを識別する為の固有の文字列
    bl_idname = "TOPBAR_MT_my_menu"
    # メニューのラベルとして表示される文字列
    bl_label = "MyMenu"
    # 著作表示名用の文字列
    bl_description = "拡張メニュー by " + bl_info["author"]

    # サブメニューの描画
    def draw(self, context):
        
        # トップバーの「エディターメニュー」に項目（オペレータ）を追加
        self.layout.operator("wm.url_open_preset", text="Manual", icon='HELP')
        # 頂点を伸ばすオペレータのボタンを追加
        self.layout.operator(MYADDON_OT_stretch_vertex.bl_idname, text=MYADDON_OT_stretch_vertex.bl_label)
        # ICO球生成オペレータのボタンを追加
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname, text=MYADDON_OT_create_ico_sphere.bl_label)
        # シーン出力オペレータのボタンを追加
        self.layout.operator(MYADDON_OT_export_scene.bl_idname, text=MYADDON_OT_export_scene.bl_label)

    # 既存のメニューにサブメニューを追加
    def submenu(self, context):

        # ID指定でサブメニューを追加
        self.layout.menu(TOPBAR_MT_my_menu.bl_idname)

# Blenderに登録するクラスリスト
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    MYADDON_OT_add_filename,
    OBJECT_PT_file_name,
    MYADDON_OT_add_collider,
    OBJECT_PT_collider,
    TOPBAR_MT_my_menu,
)

# テスト実行用コード
if __name__ == "__main__":
    register()