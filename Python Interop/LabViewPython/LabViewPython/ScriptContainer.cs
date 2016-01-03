using System;
using System.Windows.Forms;

using System.Runtime.InteropServices;
using System.Diagnostics;

namespace LabViewPython
{
    [Flags]
    enum ParentSet
    {
        None,
        Video,
        Adjustment,
        Outputs
    }

    public partial class ScriptContainer : UserControl
    {
        public static int GWL_STYLE = -16;
        public static int WS_CHILD = 0x40000000; //child window
        public static int WS_BORDER = 0x00800000; //window with border
        public static int WS_DLGFRAME = 0x00400000; //window with double border but no title
        public static int WS_CAPTION = WS_BORDER | WS_DLGFRAME; //window with a title bar

        Timer windowMon;
        Label status;
        Panel panel;
        ParentSet parentStatus;
        IntPtr prevParent;
        IntPtr currentWnd;

        public ScriptContainer()
        {
            InitializeComponent();

            AutoSize = true;
            parentStatus = ParentSet.None;
            status = new Label();
            status.Text = "Waiting for video";

            panel = new Panel();
            panel.Controls.Add(status);
            Controls.Add(panel);

            windowMon = new Timer();
            windowMon.Interval = 10;
            windowMon.Tick += CheckPythonWindows;
            windowMon.Start();

            Disposed += containerClosing;
        }

        private void containerClosing(object sender, EventArgs e)
        {
            windowMon.Stop();
            SetParent(currentWnd, prevParent);
        }

        private void CheckPythonWindows(object sender, EventArgs e)
        {
            foreach(Process proc in Process.GetProcessesByName("python"))
            {
                switch(proc.MainWindowTitle)
                {
                    case "video":
                        if (parentStatus != ParentSet.Video)
                            EmbedWindow(proc);

                        parentStatus = ParentSet.Video;
                        status.Text = "Waiting for adjustment window";
                        break;

                    case "Adjustment":
                        if (parentStatus != ParentSet.Adjustment)
                            EmbedWindow(proc);

                        parentStatus = ParentSet.Adjustment;
                        status.Text = "Waiting for outputs";
                        break;

                    case "Outputs":
                        if (parentStatus != ParentSet.Outputs)
                            EmbedWindow(proc);

                        parentStatus = ParentSet.Outputs;
                        status.Text = "Waiting for video";
                        break;
                }
            }
        }

        private void EmbedWindow(Process proc)
        {
            currentWnd = proc.MainWindowHandle;
            prevParent = GetParent(currentWnd);
            int style = GetWindowLong(currentWnd, GWL_STYLE);
            SetWindowLong(currentWnd, GWL_STYLE, (style & ~WS_CAPTION));
            SetParent(currentWnd, panel.Handle);
            RECT size;
            GetWindowRect(currentWnd, out size);
            MoveWindow(currentWnd, 0, 0, size.Width, size.Height, true);
            panel.Width = size.Width;
            panel.Height = size.Height;
        }

        #region WINAPI

        [DllImport("user32.dll")]
        static extern IntPtr SetParent(IntPtr hWndChild, IntPtr hWndNewParent);

        [DllImport("user32.dll")]
        public static extern int GetWindowLong(IntPtr hWnd, int nIndex);

        [DllImport("user32.dll")]
        private static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong);

        [DllImport("user32.dll")]
        static extern bool MoveWindow(IntPtr Handle, int x, int y, int w, int h, bool repaint);

        [DllImport("user32.dll", SetLastError = true)]
        static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);

        [DllImport("user32.dll")]
        public static extern IntPtr GetParent(IntPtr hWnd);

        #endregion
    }
}
