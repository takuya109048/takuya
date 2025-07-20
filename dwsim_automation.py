import clr
import os
import sys
import traceback
import pythoncom 
from System.Reflection import Assembly # Assemblyをインポート
from System import Convert # System.Convert をインポート
from System.IO import Directory, Path, File, MemoryStream # MemoryStreamをインポート
from System import Array, String, Environment # Array, String, Environmentをインポート

def main():
    try:
        pythoncom.CoInitialize() 

        dwsimpath = r"C:\Users\takuy\AppData\Local\DWSIM\\" # あなたのDWSIMインストールパスに合わせて修正

        try:
            clr.AddReference(os.path.join(dwsimpath, "CapeOpen.dll"))
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.Automation.dll"))
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.Interfaces.dll"))
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.GlobalSettings.dll"))
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.SharedClasses.dll"))
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.Thermodynamics.dll"))
            # DWSIM.UnitOperations.dll を参照し、後でアセンブリを直接取得するために変数に格納
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.UnitOperations.dll")) 
            dwsim_unitoperations_assembly = Assembly.LoadFrom(os.path.join(dwsimpath, "DWSIM.UnitOperations.dll")) # アセンブリを直接ロード
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.Inspector.dll"))
            clr.AddReference(os.path.join(dwsimpath, "System.Buffers.dll"))
            clr.AddReference(os.path.join(dwsimpath, "DWSIM.Thermodynamics.ThermoC.dll")) 
        except Exception as e:
            print(f"DLL参照エラー: {e}")
            print("指定された 'dwsimpath' にDLLファイルが存在するか確認してください。")
            pythoncom.CoUninitialize() 
            sys.exit(1) 

        from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType 
        from DWSIM.Thermodynamics import Streams, PropertyPackages
        from DWSIM.UnitOperations import UnitOperations 
        from DWSIM.Automation import Automation3
        from DWSIM.GlobalSettings import Settings
        from System import Array 
        from System.IO import Directory, Path, File, MemoryStream # MemoryStreamをインポート
        from System import String, Environment 
        from System import Type as DotNetType 
        
        # 以前のDLL検査結果に基づき、正しいパスから必要な型をインポート
        # Column.condtype のために必要
        from DWSIM.UnitOperations.UnitOperations import Column 
        
        # ColumnSpec.SpecType は直接使用しないため、取得は不要
        # SpecType = dwsim_unitoperations_assembly.GetType("DWSIM.UnitOperations.UnitOperations.Auxiliary.SepOps.ColumnSpec+SpecType")
        # if not SpecType:
        #     print("エラー: ColumnSpec.SpecType 型がアセンブリ内で見つかりません。")
        #     pythoncom.CoUninitialize()
        #     return


        os.environ["PATH"] += os.pathsep + dwsimpath 
        Directory.SetCurrentDirectory(dwsimpath)

        manager = Automation3()
        print("DWSIM Automation COM オブジェクト接続成功")

        myflowsheet = manager.CreateFlowsheet()
        print("新しいフローシートを作成しました。")

        cnames = ["Water", "Ethanol","Acetone"]
        myflowsheet.AddCompound("Water")
        myflowsheet.AddCompound("Ethanol")
        myflowsheet.AddCompound("Acetone")
        print("コンポーネント（水、エタノール、アセトン）を追加しました。")

        feed  = myflowsheet.AddFlowsheetObject("Material Stream", "Feed")
        dist = myflowsheet.AddFlowsheetObject("Material Stream", "Distillate")
        bottoms = myflowsheet.AddFlowsheetObject("Material Stream", "Bottoms")
        column = myflowsheet.AddFlowsheetObject("Distillation Column", "Column") 
        
        feed = feed.GetAsObject()
        dist = dist.GetAsObject()
        bottoms = bottoms.GetAsObject()
        column = column.GetAsObject()
        print("ストリームと蒸留塔を追加しました。")

        column.SetNumberOfStages(12)
        print(f"蒸留塔の段数を {column.NumberOfStages} に設定しました。")

        # ----------------------------------------------------------------------
        # ***** DistillationColumn の型を正確なフルネームで取得 *****
        # DWSIM.UnitOperations.dll アセンブリから直接型を取得する
        DistillationColumnType = dwsim_unitoperations_assembly.GetType("DWSIM.UnitOperations.UnitOperations.DistillationColumn")
        
        if not DistillationColumnType:
            # もし見つからなければ、以前のバージョン名を試す (念のため残しておく)
            DistillationColumnType = dwsim_unitoperations_assembly.GetType("DWSIM.UnitOperations.DistillationColumn")

        if not DistillationColumnType:
            print("エラー: DistillationColumn 型がアセンブリ内で見つかりません。DLLパスとフルネームを確認してください。")
            print("DWSIMのバージョンに応じて、DWSIM.UnitOperations.UnitOperations.DistillationColumn または DWSIM.UnitOperations.DistillationColumn のいずれかが必要です。")
            pythoncom.CoUninitialize() 
            return

        # 修正: 'RuntimeType' object is not callable エラーを解決するため、System.Convert.ChangeType を使用してキャスト
        distillation_column = Convert.ChangeType(column, DistillationColumnType)
        # ----------------------------------------------------------------------

        distillation_column.ConnectFeed(feed, 6) 
        distillation_column.ConnectDistillate(dist)
        distillation_column.ConnectBottoms(bottoms)
        print("ストリームを蒸留塔に接続しました。")

        myflowsheet.NaturalLayout()
        print("フローシートを自動レイアウトしました。")

        feed.SetOverallComposition(Array[float]([0.4, 0.4, 0.2])) 
        feed.SetTemperature(350.0) 
        feed.SetPressure(101325.0) 
        feed.SetMolarFlow(300.0) 
        # feed.Update() # 修正: MaterialStream オブジェクトには Update メソッドがないため削除
        # 修正: Temperature, Pressure, TotalMolarFlow の代わりにゲッターメソッドを使用
        print(f"フィードストリームを設定しました: {feed.GetTemperature()} K, {feed.GetPressure()} Pa, {feed.GetMolarFlow()} mol/s")
        
        # 修正: myflowsheet.Compounds の代わりに cnames を直接使用
        feed_comp_info = cnames 
        for i in range(len(feed_comp_info)):
            print(f"   {feed_comp_info[i]}: {feed.GetOverallComposition()[i]:.2f}")

        # ----------------------------------------------------------------------
        # SetCondenserSpecとSetReboilerSpecの引数にEnum値を使用
        # 以前のDLL検査結果に基づき、正しい列挙型メンバーを使用
        # ----------------------------------------------------------------------
        # 修正: RefluxRatio を直接設定する行を削除し、SetCondenserSpec で設定
        # distillation_column.RefluxRatio = 3.0 # この行を削除

        # 修正: SetCondenserSpec を文字列 "Reflux Ratio" を使用して呼び出す
        # 4つ目の引数は空文字列で渡す
        distillation_column.SetCondenserSpec("Reflux Ratio", 3.0, "", "") 
        
        # 修正: Product_Molar_Flow_Rate を文字列リテラルとして渡す
        distillation_column.SetReboilerSpec("Product_Molar_Flow_Rate", 200.0, "mol/s") 
        print("蒸留塔の仕様を設定しました。")

        nrtl = myflowsheet.CreateAndAddPropertyPackage("NRTL")
        print(f"プロパティパッケージ '{nrtl.Name}' を作成し追加しました。")

        print("シミュレーション計算中...")
        errors = manager.CalculateFlowsheet4(myflowsheet)
        
        if errors.Count == 0:
            print("シミュレーション計算成功！")
        else:
            print("シミュレーション計算失敗。エラー詳細:")
            for error in errors:
                print(f"   - {error.Message}")
            pythoncom.CoUninitialize() 
            return 

        print("\n--- シミュレーション結果 ---")
        cduty = distillation_column.CondenserDuty
        rduty = distillation_column.ReboilerDuty
        print(f"Condenser Duty: {cduty:.2f} kW")
        print(f"Reboiler Duty: {rduty:.2f} kW")

        dtemp = dist.GetTemperature()
        dflow = dist.GetMolarFlow()
        btemp = bottoms.GetTemperature()
        bflow = bottoms.GetMolarFlow()
        
        print(f"\nDistillate Temperature: {dtemp:.2f} K")
        print(f"Bottoms Temperature: {btemp:.2f} K")
        print(f"\nDistillate Molar Flow: {dflow:.2f} mol/s")
        print(f"Bottoms Molar Flow: {bflow:.2f} mol/s")

        distcomp = dist.GetOverallComposition()
        print("\nDistillate Molar Composition:")
        for i in range(len(cnames)): 
            print(f"   {cnames[i]}: {distcomp[i]:.4f}")
        
        bcomp = bottoms.GetOverallComposition()
        print("\nBottoms Molar Composition:")
        for i in range(len(cnames)): 
            print(f"   {cnames[i]}: {bcomp[i]:.4f}")

        fileNameToSave = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "python_column_sample.dwxmz")
        manager.SaveFlowsheet(myflowsheet, fileNameToSave, True)
        print(f"\nフローシートを '{fileNameToSave}' に保存しました。")

        # PFD画像の保存と表示に関する修正
        stream = None # stream変数を初期化
        try:
            clr.AddReference(os.path.join(dwsimpath, "SkiaSharp.dll"))
            clr.AddReference("System.Drawing") 

            from SkiaSharp import SKBitmap, SKImage, SKCanvas, SKEncodedImageFormat
            from System.IO import MemoryStream
            from System.Drawing import Image
            from System.Drawing.Imaging import ImageFormat
            from PIL import Image as PILImage 

            PFDSurface = myflowsheet.GetSurface()
            imgwidth = 1024
            imgheight = 768
            bmp = SKBitmap(imgwidth, imgheight)
            canvas = SKCanvas(bmp)
            PFDSurface.Center(imgwidth, imgheight)
            PFDSurface.ZoomAll(imgwidth, imgheight)
            PFDSurface.UpdateCanvas(canvas)
            d = SKImage.FromBitmap(bmp).Encode(SKEncodedImageFormat.Png, 100)
            
            # 修正: withステートメントを削除し、MemoryStreamを明示的に閉じる
            stream = MemoryStream()
            d.SaveTo(stream)
            image = Image.FromStream(stream)
            imgPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "pfd.png")
            image.Save(imgPath, ImageFormat.Png)
            
            canvas.Dispose()
            bmp.Dispose()
            
            print(f"PFD画像を '{imgPath}' に保存しました。")
            im = PILImage.open(imgPath)
            im.show() 
            print("PFD画像を表示しました。")

        except Exception as img_e:
            print(f"\nPFD画像保存/表示エラー: {img_e}")
            print("SkiaSharp.dll や System.Drawing.dll の参照、または Pillow のインストールを確認してください。")
            traceback.print_exc()
        finally:
            if stream:
                stream.Dispose() # MemoryStreamを明示的にDispose

    except Exception as e:
        print(f"\n致命的なエラーが発生しました: {e}")
        traceback.print_exc()
    finally:
        pythoncom.CoUninitialize() 

if __name__ == "__main__":
    main()
