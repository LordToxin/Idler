Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)
strCmd = """" & "C:\Users\Max\AppData\Local\Programs\Python\Python313\pythonw.exe" & """ """ & strDir & "\farmer.py"""
WshShell.CurrentDirectory = strDir
WshShell.Run strCmd, 0, False
