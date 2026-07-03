Option Explicit

' Double-click launcher for Windows. It runs the existing bootstrap script
' with its console window hidden; SpeechTyper itself already uses pythonw.
Dim shell, fileSystem, projectDir, command, exitCode, logFile
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

projectDir = fileSystem.GetParentFolderName(WScript.ScriptFullName)
command = "cmd.exe /d /s /c " & Chr(34) & Chr(34) _
    & projectDir & "\run.bat" & Chr(34) & Chr(34)
logFile = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") _
    & "\SpeechTyper\launcher.log"

exitCode = shell.Run(command, 0, True)
If exitCode <> 0 Then
    shell.Popup "SpeechTyper could not start." & vbCrLf & vbCrLf _
        & "Details: " & logFile, 0, "SpeechTyper", 16
End If
