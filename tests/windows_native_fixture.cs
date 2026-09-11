// Tiny native-process fixture: no Python launcher and no application build.
using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
public class WindowsStartupFixture {
    static string Q(string text) { return "\"" + text.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\""; }
    public static int Main(string[] args) {
        if (args.Length > 0 && args[0] == "--hold-output") {
            Console.WriteLine("child holding inherited stdout");
            Console.Error.WriteLine("child holding inherited stderr");
            Thread.Sleep(30000);
            return 0;
        }
        string exe = Process.GetCurrentProcess().MainModule.FileName;
        string calls = Environment.GetEnvironmentVariable("MARS_TEST_CALLS");
        if (!String.IsNullOrEmpty(calls)) File.AppendAllText(calls, String.Join(" ", args) + "\n");
        if (args.Length > 0 && args[0] == "-I") {
            string prefix = Path.GetDirectoryName(Path.GetDirectoryName(exe));
            string version = Environment.GetEnvironmentVariable("MARS_TEST_VERSION") ?? "3,12,10";
            string bits = Environment.GetEnvironmentVariable("MARS_TEST_BITS") ?? "64";
            string declared = Environment.GetEnvironmentVariable("VIRTUAL_ENV") ?? Environment.GetEnvironmentVariable("CONDA_PREFIX");
            Console.WriteLine("{\"executable\":" + Q(exe) + ",\"prefix\":" + Q(prefix) + ",\"declared\":" + Q(declared) + ",\"version\":[" + version + "],\"machine\":\"AMD64\",\"bits\":" + bits + "}");
            Console.Error.WriteLine("harmless interpreter warning");
            return 0;
        }
        string mode = Environment.GetEnvironmentVariable("MARS_TEST_MODE") ?? "success";
        if (Path.GetFileName(exe) == "windowed.exe") mode = Environment.GetEnvironmentVariable("MARS_TEST_WINDOWED_MODE") ?? mode;
        Console.WriteLine("fixture stdout");
        Console.Error.WriteLine("fixture stderr");
        if (args.Length == 0 || args[0] != "--smoke-test") {
            return Int32.Parse(Environment.GetEnvironmentVariable("MARS_TEST_EXIT") ?? "23");
        }
        if (mode == "pre-python") { Console.Error.WriteLine("Failed to start embedded python interpreter!\nFatal Python error: init_fs_encoding\nModuleNotFoundError: encodings"); return 1; }
        if (mode == "no-report") return 0;
        if (mode == "early-child" || mode == "ready-child") {
            var child = Process.Start(new ProcessStartInfo(exe, "--hold-output") {
                UseShellExecute = false, CreateNoWindow = true
            });
            File.WriteAllText(Environment.GetEnvironmentVariable("MARS_TEST_CHILD_FILE"), child.Id.ToString());
            if (mode == "early-child") return 0;
        }
        string report = args[2];
        int pid = Process.GetCurrentProcess().Id;
        if (mode == "wrong-pid") pid++;
        string status = mode == "failure" ? "failed" : "ready";
        File.WriteAllText(report, "{\"protocol\":\"mars-startup-v1\",\"status\":" + Q(status) + ",\"phase\":\"event-loop-complete\",\"executable\":" + Q(exe) + ",\"pid\":" + pid + "}");
        if (mode == "stall") Thread.Sleep(30000);
        if (mode == "failure") { Console.Error.WriteLine("Traceback: fixture import failure"); return 7; }
        return 0;
    }
}
