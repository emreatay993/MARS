# Shared by the build entry point and the Python-free packaged diagnostic runner.
# Windows PowerShell 5.1 and PowerShell 7. No execution-policy changes.
function Read-RunOptions {
    param([object[]]$Arguments, [string[]]$Switches, [string[]]$Values)
    $options = @{}
    for ($i = 0; $i -lt $Arguments.Count; $i++) {
        $key = ([string]$Arguments[$i]).TrimStart('-').Replace('-', '').ToLowerInvariant()
        if ($key -in $Switches) { $options[$key] = $true }
        elseif ($key -in $Values) {
            $i++
            if ($i -ge $Arguments.Count -or [string]::IsNullOrWhiteSpace($Arguments[$i])) {
                throw "Missing value for $key."
            }
            $options[$key] = [string]$Arguments[$i]
        }
        else { throw "Unknown option: $($Arguments[$i]). Use -Help." }
    }
    return $options
}

function Wait-RunPrompt {
    param([bool]$NoPause)
    if (-not $NoPause) {
        Write-Host 'Press Enter to close'
        try { $null = Read-Host }
        catch { Write-Host "Unable to read Enter: $($_.Exception.Message)" }
    }
}

function Get-FullPath {
    param([string]$Path)
    # PowerShell Set-Location does not update the process current directory.
    $full = [IO.Path]::GetFullPath($ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path))
    if ($full.Length -gt [IO.Path]::GetPathRoot($full).Length) { return $full.TrimEnd('\', '/') }
    return $full
}

function Test-PathWithin {
    param([string]$Path, [string]$Parent)
    $p = Get-FullPath $Path
    $root = Get-FullPath $Parent
    return $p.Equals($root, [StringComparison]::OrdinalIgnoreCase) -or
        $p.StartsWith($root.TrimEnd('\', '/') + '\', [StringComparison]::OrdinalIgnoreCase)
}

function Assert-NoReparsePath {
    param([string]$Path, [switch]$Recurse)
    $cursor = Get-FullPath $Path
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Refusing reparse point: $cursor"
            }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    if ($Recurse -and (Test-Path -LiteralPath $Path -PathType Container)) {
        # Walk one level at a time; never follow a junction before checking it.
        foreach ($child in Get-ChildItem -LiteralPath $Path -Force) {
            if ($child.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Refusing reparse point: $($child.FullName)"
            }
            if ($child.PSIsContainer) { Assert-NoReparsePath $child.FullName -Recurse }
        }
    }
}

function Assert-BuildTarget {
    param([string]$Target, [string]$Expected, [string]$EnvironmentPath)
    if (-not (Get-FullPath $Target).Equals((Get-FullPath $Expected), [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unexpected build target: $Target (expected $Expected)"
    }
    if ((Test-PathWithin $EnvironmentPath $Target) -or (Test-PathWithin $Target $EnvironmentPath)) {
        throw "Build target overlaps the active environment: $Target / $EnvironmentPath"
    }
    Assert-NoReparsePath $Target -Recurse
}

function New-RunLogDirectory {
    param([string]$Parent)
    Assert-NoReparsePath $Parent
    $id = (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
    $path = Join-Path $Parent $id
    $null = New-Item -ItemType Directory -Path $path -Force
    return $path
}

function ConvertTo-NativeArgument {
    param([string]$Value)
    # Windows CommandLineToArgvW/CRT quoting, including trailing backslashes.
    return '"' + [regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
}

function Start-LoggedProcess {
    param([string]$Executable, [string[]]$Arguments, [string]$Directory, [string]$LogPrefix)
    Write-Host "Executable: $Executable"
    Write-Host "stdout: $LogPrefix.stdout.log"
    Write-Host "stderr: $LogPrefix.stderr.log"
    $commandLine = ($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
    $parameters = @{
        FilePath = $Executable; WorkingDirectory = $Directory; PassThru = $true
        WindowStyle = 'Hidden'; RedirectStandardOutput = "$LogPrefix.stdout.log"
        RedirectStandardError = "$LogPrefix.stderr.log"
    }
    if ($commandLine) { $parameters.ArgumentList = $commandLine }
    $process = Start-Process @parameters
    # Retain a process handle before waiting. Windows PowerShell 5.1 otherwise
    # exposes a null ExitCode for a Start-Process -PassThru process after exit.
    $null = $process.Handle
    return $process
}

function Invoke-LoggedProcess {
    param([string]$Executable, [string[]]$Arguments, [string]$Directory, [string]$LogPrefix)
    $process = Start-LoggedProcess $Executable $Arguments $Directory $LogPrefix
    try {
        $process.WaitForExit()
        $code = $process.ExitCode
        if ($null -eq $code) { throw "Cannot determine native exit status: $Executable" }
        # Read stderr as ordinary text. PS 5.1 native stderr must not become an ErrorRecord.
        foreach ($file in @("$LogPrefix.stdout.log", "$LogPrefix.stderr.log")) {
            if (Test-Path -LiteralPath $file) { Get-Content -LiteralPath $file | ForEach-Object { Write-Host $_ } }
        }
        if ($code -ne 0) {
            $errorObject = New-Object System.Exception("Native command exited ${code}: $Executable; logs: $LogPrefix.*.log")
            $errorObject.Data['ExitCode'] = $code
            throw $errorObject
        }
    }
    finally { $process.Dispose() }
}

function Get-RuntimeHash {
    param([string]$Path)
    # Use .NET directly; no optional module discovery or inherited PSModulePath.
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}

function Get-ActiveBuildPython {
    param([string]$Directory, [string]$LogDirectory)
    $prefix = $env:VIRTUAL_ENV
    $kind = 'VIRTUAL_ENV'
    if (-not $prefix -and $env:CONDA_PREFIX) { $prefix = $env:CONDA_PREFIX; $kind = 'CONDA_PREFIX' }
    if (-not $prefix) { throw 'No active environment. Manually activate a Python 3.12 x64 environment before building.' }
    $prefix = Get-FullPath $prefix
    Write-Host "Active environment ($kind): $prefix"
    if (-not (Test-Path -LiteralPath $prefix -PathType Container)) { throw "Environment does not exist: $prefix" }
    $command = Get-Command python.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $python = $command.Source
    Write-Host "PATH interpreter: $python"
    $probe = Join-Path $LogDirectory 'interpreter'
    Invoke-LoggedProcess $python @('-I', '-c', 'import json,sys,struct,os,platform; print(json.dumps(dict(executable=os.path.realpath(sys.executable),prefix=os.path.realpath(sys.prefix),version=list(sys.version_info[:3]),bits=struct.calcsize("P")*8,machine=platform.machine(),declared=os.path.realpath(os.environ.get("VIRTUAL_ENV") or os.environ["CONDA_PREFIX"]))))') $Directory $probe
    $info = Get-Content -LiteralPath "$probe.stdout.log" -Raw | ConvertFrom-Json
    Write-Host "Interpreter: $($info.executable)"
    Write-Host "Python: $($info.version -join '.') / $($info.bits)-bit / $($info.machine)"
    Write-Host "sys.prefix: $($info.prefix)"
    if (-not (Get-FullPath $info.prefix).Equals((Get-FullPath $info.declared), [StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-PathWithin $info.executable $info.prefix) -or -not (Test-PathWithin $python $prefix)) {
        throw 'Active environment does not match PATH python.exe, sys.executable and sys.prefix. Activate the intended environment again.'
    }
    if ($info.version[0] -ne 3 -or $info.version[1] -ne 12 -or $info.bits -ne 64 -or $info.machine -notin @('AMD64', 'x86_64')) {
        throw 'Build requires Python 3.12 x64; dependency installation has not started.'
    }
    return $info
}

function Start-DiagnosticProcess {
    param([string]$Executable, [string[]]$Arguments, [string]$Directory, [string]$LogPrefix)
    # Create suspended, assign to a private job, then resume. Native file handles
    # avoid asynchronous .NET stream drains that can wait on surviving children.
    if (-not ('MarsStartup.OwnedProcess' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
namespace MarsStartup {
    public sealed class OwnedProcess : IDisposable {
        [StructLayout(LayoutKind.Sequential)] struct Basic {
            public long ProcessTime, JobTime; public uint Flags;
            public UIntPtr MinWorkingSet, MaxWorkingSet; public uint ActiveProcessLimit;
            public UIntPtr Affinity; public uint PriorityClass, SchedulingClass;
        }
        [StructLayout(LayoutKind.Sequential)] struct Io {
            public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes;
        }
        [StructLayout(LayoutKind.Sequential)] struct Extended {
            public Basic Basic; public Io Io;
            public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
        }
        [StructLayout(LayoutKind.Sequential)] struct Security {
            public int Length; public IntPtr Descriptor; public int Inherit;
        }
        [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Startup {
            public int Size; public string Reserved, Desktop, Title;
            public uint X, Y, XSize, YSize, XChars, YChars, Fill, Flags;
            public ushort Show, ReservedSize; public IntPtr ReservedBytes, Input, Output, Error;
        }
        [StructLayout(LayoutKind.Sequential)] struct StartupEx {
            public Startup Startup; public IntPtr Attributes;
        }
        [StructLayout(LayoutKind.Sequential)] struct ProcessInfo {
            public IntPtr Process, Thread; public uint ProcessId, ThreadId;
        }
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        static extern IntPtr CreateJobObject(IntPtr attributes, string name);
        [DllImport("kernel32.dll", SetLastError=true)]
        static extern bool SetInformationJobObject(IntPtr job, int type, ref Extended info, uint size);
        [DllImport("kernel32.dll", SetLastError=true)]
        static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        static extern IntPtr CreateFile(string path, uint access, uint share, ref Security security,
            uint disposition, uint attributes, IntPtr template);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        static extern bool CreateProcess(string exe, StringBuilder command, IntPtr processAttributes,
            IntPtr threadAttributes, bool inherit, uint flags, IntPtr environment, string directory,
            ref StartupEx startup, out ProcessInfo process);
        [DllImport("kernel32.dll", SetLastError=true)]
        static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, int flags, ref IntPtr size);
        [DllImport("kernel32.dll", SetLastError=true)]
        static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, IntPtr attribute, IntPtr value,
            IntPtr size, IntPtr previous, IntPtr returned);
        [DllImport("kernel32.dll")] static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("kernel32.dll", SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll", SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
        [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process, out uint code);
        [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateProcess(IntPtr process, uint code);
        [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
        IntPtr job, handle;
        Process windowProcess;
        public int Id { get; private set; }
        private OwnedProcess() {}
        static IntPtr OpenRedirect(string path, uint access, uint disposition) {
            var security = new Security(); security.Length = Marshal.SizeOf(security); security.Inherit = 1;
            var file = CreateFile(path, access, 3, ref security, disposition, 0x80, IntPtr.Zero);
            if (file == new IntPtr(-1)) throw new Win32Exception();
            return file;
        }
        public static OwnedProcess Start(string exe, string command, string directory, string stdout, string stderr) {
            var owned = new OwnedProcess();
            IntPtr output = IntPtr.Zero, error = IntPtr.Zero, input = IntPtr.Zero;
            IntPtr attributes = IntPtr.Zero, handles = IntPtr.Zero, thread = IntPtr.Zero;
            bool initialized = false;
            try {
                owned.job = CreateJobObject(IntPtr.Zero, null);
                if (owned.job == IntPtr.Zero) throw new Win32Exception();
                var limits = new Extended(); limits.Basic.Flags = 0x2000; // KILL_ON_JOB_CLOSE
                if (!SetInformationJobObject(owned.job, 9, ref limits, (uint)Marshal.SizeOf(limits))) throw new Win32Exception();
                output = OpenRedirect(stdout, 0x40000000, 2);
                error = OpenRedirect(stderr, 0x40000000, 2);
                input = OpenRedirect("NUL", 0x80000000, 3);
                IntPtr size = IntPtr.Zero;
                InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref size);
                attributes = Marshal.AllocHGlobal(size);
                if (!InitializeProcThreadAttributeList(attributes, 1, 0, ref size)) throw new Win32Exception();
                initialized = true;
                handles = Marshal.AllocHGlobal(3 * IntPtr.Size);
                Marshal.WriteIntPtr(handles, 0, input);
                Marshal.WriteIntPtr(handles, IntPtr.Size, output);
                Marshal.WriteIntPtr(handles, 2 * IntPtr.Size, error);
                // Inherit only these three handles, never unrelated host handles.
                if (!UpdateProcThreadAttribute(attributes, 0, new IntPtr(0x20002), handles,
                    new IntPtr(3 * IntPtr.Size), IntPtr.Zero, IntPtr.Zero)) throw new Win32Exception();
                var startup = new StartupEx(); startup.Startup.Size = Marshal.SizeOf(startup);
                startup.Startup.Flags = 0x101; // USESTDHANDLES | USESHOWWINDOW (hidden)
                startup.Startup.Input = input; startup.Startup.Output = output; startup.Startup.Error = error;
                startup.Attributes = attributes;
                ProcessInfo info;
                // SUSPENDED | NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT
                if (!CreateProcess(exe, new StringBuilder(command), IntPtr.Zero, IntPtr.Zero, true,
                    0x08080004, IntPtr.Zero, directory, ref startup, out info)) throw new Win32Exception();
                owned.handle = info.Process; thread = info.Thread; owned.Id = (int)info.ProcessId;
                if (!AssignProcessToJobObject(owned.job, owned.handle)) throw new Win32Exception();
                owned.windowProcess = Process.GetProcessById(owned.Id);
                var retainedHandle = owned.windowProcess.Handle;
                if (ResumeThread(thread) == UInt32.MaxValue) throw new Win32Exception();
                return owned;
            }
            catch {
                // Also covers assignment failure while the child is still suspended.
                if (owned.handle != IntPtr.Zero) TerminateProcess(owned.handle, 1);
                owned.Dispose(); throw;
            }
            finally {
                if (thread != IntPtr.Zero) CloseHandle(thread);
                if (initialized) DeleteProcThreadAttributeList(attributes);
                if (attributes != IntPtr.Zero) Marshal.FreeHGlobal(attributes);
                if (handles != IntPtr.Zero) Marshal.FreeHGlobal(handles);
                if (input != IntPtr.Zero) CloseHandle(input);
                if (output != IntPtr.Zero) CloseHandle(output);
                if (error != IntPtr.Zero) CloseHandle(error);
            }
        }
        public bool WaitForExit(int milliseconds) {
            if (milliseconds < 0) throw new ArgumentOutOfRangeException("milliseconds");
            uint result = WaitForSingleObject(handle, (uint)milliseconds);
            if (result == UInt32.MaxValue) throw new Win32Exception();
            return result == 0;
        }
        public bool HasExited { get { return WaitForExit(0); } }
        public int ExitCode {
            get {
                if (!HasExited) throw new InvalidOperationException("Process is still running");
                uint code; if (!GetExitCodeProcess(handle, out code)) throw new Win32Exception();
                return unchecked((int)code);
            }
        }
        public bool CloseMainWindow() { return !HasExited && windowProcess.CloseMainWindow(); }
        public void Kill() {
            if (!HasExited && !TerminateProcess(handle, 1) && !HasExited) throw new Win32Exception();
        }
        public void Dispose() {
            // Closing the private job kills remaining descendants and releases
            // their file handles. No managed stdout/stderr draining occurs.
            if (job != IntPtr.Zero) { CloseHandle(job); job = IntPtr.Zero; }
            if (windowProcess != null) { windowProcess.Dispose(); windowProcess = null; }
            if (handle != IntPtr.Zero) { CloseHandle(handle); handle = IntPtr.Zero; }
        }
    }
}
'@
    }
    Write-Host "Executable: $Executable"
    Write-Host "stdout: $LogPrefix.stdout.log"
    Write-Host "stderr: $LogPrefix.stderr.log"
    $commandLine = ((@($Executable) + $Arguments) | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
    return [MarsStartup.OwnedProcess]::Start($Executable, $commandLine, $Directory, "$LogPrefix.stdout.log", "$LogPrefix.stderr.log")
}
