import wx
import requests
import io
import datetime
import threading
import json
import webbrowser
import gui
import ui
import globalPluginHandler
import addonHandler
import inputCore
from scriptHandler import script
from typing import Optional
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import uuid

addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("AI Image Generator")

    def __init__(self):
        super().__init__()
        self.toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
        self.menuItem = self.toolsMenu.Append(
            wx.ID_ANY,
            _("AI Image Generator"),
            _("Generate images using AI")
        )
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onShowDialog, self.menuItem)

    def terminate(self):
        try:
            self.toolsMenu.Remove(self.menuItem.GetId())
        except Exception:
            pass

    @script(
        description=_("Opens the AI Image Generator add-on"),
        gesture="kb:NVDA+shift+a"
    )
    def script_openAIImageGenerator(self, gesture):
        wx.CallAfter(self.onShowDialog, None)

    def onShowDialog(self, evt):
        wx.CallAfter(gui.mainFrame.prePopup)
        try:
            dlg = AIImageGeneratorDialog(gui.mainFrame)
            dlg.Show()
        finally:
            wx.CallAfter(gui.mainFrame.postPopup)

class AIImageGeneratorDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("AI Image Generator"), size=(800, 600))
        self.panel = wx.Panel(self)
        self.api_url = "https://image.pollinations.ai/prompt/"
        self.current_image = None
        self.last_prompt = ""
        self.is_processing = False
        self.result_queue = Queue()
        self.thread_pool = ThreadPoolExecutor(max_workers=1)
        self.processing_dlg = None

        # GUI Components
        self.prompt_label = wx.StaticText(self.panel, label=_("Enter your imagination here..."))
        self.prompt_input = wx.TextCtrl(
            self.panel,
            style=wx.TE_MULTILINE,
            size=(700, 100)
        )
        self.clear_btn = wx.Button(self.panel, label=_("&Clear"), id=wx.ID_CLEAR)
        self.about_btn = wx.Button(self.panel, label=_("&About"), id=wx.ID_ABOUT)
        self.generate_btn = wx.Button(self.panel, label=_("&Generate Image"), id=wx.ID_APPLY)
        self.close_btn = wx.Button(self.panel, label=_("C&lose"), id=wx.ID_CLOSE)
        self.image_display = wx.StaticBitmap(self.panel)
        self.clear_btn.Hide()

        # Layout
        self.setup_layout()

        # Bind Events
        self.bind_events()

        # Set Theme
        self.set_theme()

        # Set focus to input
        self.prompt_input.SetFocus()

    def setup_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.prompt_label, 0, wx.ALL, 5)
        sizer.Add(self.prompt_input, 0, wx.ALL | wx.EXPAND, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.clear_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.about_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.generate_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.close_btn, 0, wx.RIGHT, 5)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)
        sizer.Add(self.image_display, 1, wx.ALL | wx.EXPAND, 10)
        self.panel.SetSizer(sizer)

    def bind_events(self):
        self.prompt_input.Bind(wx.EVT_TEXT, self.on_text_change)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        self.about_btn.Bind(wx.EVT_BUTTON, self.on_about)
        self.generate_btn.Bind(wx.EVT_BUTTON, self.on_generate)
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Shortcut keys
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('C'), wx.ID_CLOSE),
            (wx.ACCEL_ALT, ord('A'), wx.ID_ABOUT),
            (wx.ACCEL_ALT, ord('G'), wx.ID_APPLY),
            (wx.ACCEL_ALT, ord('R'), wx.ID_CLEAR)
        ])
        self.SetAcceleratorTable(accel_tbl)

        # Timer to check queue
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.process_result, self.timer)

    def set_theme(self):
        bg_color = wx.Colour(244, 244, 244)
        text_color = wx.Colour(0, 0, 0)
        btn_color = wx.Colour(106, 17, 203)

        self.panel.SetBackgroundColour(bg_color)
        for child in self.panel.GetChildren():
            if isinstance(child, (wx.StaticText, wx.TextCtrl)):
                child.SetForegroundColour(text_color)
                child.SetBackgroundColour(bg_color)
            elif isinstance(child, wx.Button):
                child.SetBackgroundColour(btn_color)
                child.SetForegroundColour(wx.Colour(255, 255, 255))
        self.Refresh()

    def on_text_change(self, event):
        text = self.prompt_input.GetValue().strip()
        wx.CallAfter(self.clear_btn.Show, bool(text))
        wx.CallAfter(self.panel.Layout)

    def on_clear(self, event):
        self.prompt_input.SetValue("")
        self.image_display.SetBitmap(wx.Bitmap())
        self.current_image = None
        self.last_prompt = ""
        wx.CallAfter(self.clear_btn.Hide)
        wx.CallAfter(self.panel.Layout)
        ui.message(_("Input cleared."))

    def on_about(self, event):
        about_dlg = AboutDialog(self)
        about_dlg.ShowModal()
        about_dlg.Destroy()

    def on_generate(self, event):
        prompt = self.prompt_input.GetValue().strip()
        if not prompt:
            wx.CallAfter(wx.MessageBox, _("Please enter a valid description."), _("Error"), wx.OK | wx.ICON_ERROR)
            ui.message(_("No valid description entered."))
            return
        self.last_prompt = prompt
        self.generate_btn.Enable(False)
        self.is_processing = True
        self.processing_dlg = ProcessingDialog(self)
        wx.CallAfter(self.processing_dlg.Show)
        self.timer.Start(100)  # Start checking queue
        self.thread_pool.submit(self.generate_image, prompt)

    def generate_image(self, prompt: str):
        headers = {
            "Content-Type": "application/json",
            "Accept": "image/*"
        }
        payload = {
            "prompt": prompt,
            "model": "flux",
            "enhance": True,
            "nologo": True
        }

        try:
            with requests.Session() as session:
                response = session.post(
                    f"{self.api_url}{prompt}",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=30
                )
                response.raise_for_status()

                content_type = response.headers.get('content-type', 'image/png')
                if 'png' in content_type:
                    image_type = wx.BITMAP_TYPE_PNG
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    image_type = wx.BITMAP_TYPE_JPEG
                elif 'bmp' in content_type:
                    image_type = wx.BITMAP_TYPE_BMP
                else:
                    raise ValueError("Unsupported image format")

                image_stream = io.BytesIO(response.content)
                wx_image = wx.Image(image_stream, image_type)
                if not wx_image.IsOk():
                    raise ValueError("Invalid image data")
                self.current_image = wx_image
                self.result_queue.put(("success", wx_image))
        except (requests.RequestException, ValueError) as e:
            self.result_queue.put(("error", f"Error generating image: {str(e)}"))

    def process_result(self, event):
        if self.result_queue.empty():
            return
        try:
            result_type, result = self.result_queue.get_nowait()
            self.timer.Stop()
            if self.processing_dlg:
                wx.CallAfter(self.processing_dlg.Destroy)
                self.processing_dlg = None
            if result_type == "success":
                wx.CallAfter(self.show_image_dialog, result)
            else:
                wx.CallAfter(self.show_error, result)
        finally:
            self.is_processing = False
            wx.CallAfter(self.generate_btn.Enable, True)

    def show_image_dialog(self, wx_image: wx.Image):
        image_dlg = ImageGenerationDialog(self, wx_image)
        image_dlg.ShowModal()
        image_dlg.Destroy()

    def show_error(self, message: str):
        wx.MessageBox(message, _("Error"), wx.OK | wx.ICON_ERROR)
        ui.message(_("Image generation failed."))

    def on_close(self, event):
        if self.is_processing:
            wx.MessageBox(
                _("Please wait for the image generation to complete."),
                _("Warning"),
                wx.OK | wx.ICON_WARNING
            )
            ui.message(_("Cannot close while generating image."))
            return
        self.timer.Stop()
        self.thread_pool.shutdown(wait=True)
        self.Destroy()

class ProcessingDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Please Wait..."))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(
            wx.StaticText(self, label=_("AI is generating...")),
            0, wx.ALL | wx.CENTER, 10
        )
        self.SetSizer(sizer)
        self.Fit()
        self.CenterOnParent()
        ui.message(_("Generating image, please wait."))

class ImageGenerationDialog(wx.Dialog):
    def __init__(self, parent, wx_image: wx.Image):
        super().__init__(parent, title=_("Generated Image"))
        self.panel = wx.Panel(self)
        self.wx_image = wx_image

        # GUI Components
        self.image_display = wx.StaticBitmap(self.panel)
        self.download_btn = wx.Button(self.panel, label=_("&Download Image"), id=wx.ID_SAVE)
        self.close_btn = wx.Button(self.panel, label=_("C&lose"), id=wx.ID_CLOSE)

        # Layout
        self.setup_layout()

        # Bind Events
        self.bind_events()

        # Display Image
        self.display_image(wx_image)

    def setup_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(
            wx.StaticText(
                self.panel,
                label=_("Here is your described image generated with AI...")
            ),
            0, wx.ALL | wx.CENTER, 10
        )
        sizer.Add(self.image_display, 1, wx.ALL | wx.EXPAND, 10)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.download_btn, 0, wx.RIGHT | wx.ALL, 5)
        btn_sizer.Add(self.close_btn, 0, wx.RIGHT | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)
        self.panel.SetSizer(sizer)

    def bind_events(self):
        self.download_btn.Bind(wx.EVT_BUTTON, self.on_download)
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Shortcut keys
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('D'), wx.ID_SAVE),
            (wx.ACCEL_ALT, ord('C'), wx.ID_CLOSE)
        ])
        self.SetAcceleratorTable(accel_tbl)

    def display_image(self, wx_image: wx.Image):
        display_size = self.image_display.GetSize()
        img_width, img_height = wx_image.GetSize()
        scale = min(display_size[0] / img_width, display_size[1] / img_height, 1.0)
        new_width, new_height = int(img_width * scale), int(img_height * scale)
        scaled_image = wx_image.Scale(new_width, new_height, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(scaled_image)
        self.image_display.SetBitmap(bitmap)
        self.panel.Layout()
        ui.message(_("Image generated successfully."))

    def on_download(self, event):
        if not self.wx_image or not self.wx_image.IsOk():
            wx.MessageBox(_("No image to download."), _("Error"), wx.OK | wx.ICON_ERROR)
            ui.message(_("No image available to download."))
            return

        wildcard = "PNG files (*.png)|*.png|JPEG files (*.jpg;*.jpeg)|*.jpg;*.jpeg|BMP files (*.bmp)|*.bmp"
        with wx.FileDialog(
            self,
            _("Save Image"),
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_OK:
                path = fileDialog.GetPath()
                try:
                    extension = path.lower().split('.')[-1]
                    if extension == 'png':
                        bitmap_type = wx.BITMAP_TYPE_PNG
                    elif extension in ('jpg', 'jpeg'):
                        bitmap_type = wx.BITMAP_TYPE_JPEG
                    elif extension == 'bmp':
                        bitmap_type = wx.BITMAP_TYPE_BMP
                    else:
                        wx.MessageBox(
                            _("Unsupported file format."),
                            _("Error"),
                            wx.OK | wx.ICON_ERROR
                        )
                        ui.message(_("Unsupported file format selected."))
                        return

                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        path = f"{path}_AI_Generated_{timestamp}.{extension}"

                    self.wx_image.SaveFile(path, bitmap_type)
                    wx.MessageBox(
                        _("Image saved as {}").format(path),
                        _("Success"),
                        wx.OK | wx.ICON_INFORMATION
                    )
                    ui.message(_("Image saved successfully to {}.").format(path))
                except Exception as e:
                    wx.MessageBox(
                        _("Error saving image: {}").format(str(e)),
                        _("Error"),
                        wx.OK | wx.ICON_ERROR
                    )
                    ui.message(_("Failed to save image."))

    def on_close(self, event):
        self.Destroy()

class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("About the Add-on"))
        panel = wx.Panel(self)
        message = _(
            "AI Image Generator, v0.23, developed by Sujan Rai at Team of Tech Visionary.\n"
            "Join my Telegram channel for accessible and unique resources.\n"
            "Visit my website to browse very useful and powerful tutorials on the web."
        )
        text = wx.StaticText(panel, label=message)
        no_thanks_btn = wx.Button(panel, label=_("&No Thanks"), id=wx.ID_CANCEL)
        telegram_btn = wx.Button(panel, label=_("&Join Telegram"), id=wx.ID_ANY)
        website_btn = wx.Button(panel, label=_("Visit &Website"), id=wx.ID_ANY)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text, 0, wx.ALL | wx.CENTER, 10)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(no_thanks_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(telegram_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(website_btn, 0, wx.RIGHT, 5)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)
        panel.SetSizer(sizer)
        self.Fit()
        self.CenterOnParent()

        # Bind Events
        no_thanks_btn.Bind(wx.EVT_BUTTON, self.on_close)
        telegram_btn.Bind(wx.EVT_BUTTON, self.on_join_telegram)
        website_btn.Bind(wx.EVT_BUTTON, self.on_visit_website)

        # Shortcut keys
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('N'), wx.ID_CANCEL),
            (wx.ACCEL_ALT, ord('J'), telegram_btn.GetId()),
            (wx.ACCEL_ALT, ord('W'), website_btn.GetId())
        ])
        self.SetAcceleratorTable(accel_tbl)

    def on_join_telegram(self, event):
        webbrowser.open("https://t.me/techvisionary")
        self.Destroy()

    def on_visit_website(self, event):
        webbrowser.open("https://techvisionarytutorials.blogspot.com")
        self.Destroy()

    def on_close(self, event):
        self.Destroy()
