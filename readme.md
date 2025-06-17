# AI Image Generator NVDA Add-on

## Overview

The **AI Image Generator** is an NVDA add-on that enables users to generate images using AI by providing text prompts. It integrates seamlessly with NVDA, offering an accessible interface for visually impaired users to create and download AI-generated images.

**Developed by** : Sujan Rai at Team of Tech Visionary  
**Version** : 0.23

* * *

## Features

  * 🎧 **Accessible Interface** : Fully compatible with the NVDA screen reader.
  * 🖼️ **Text-to-Image Generation** : Generate images by entering descriptive text prompts.
  * 💾 **Image Download** : Save generated images in PNG, JPEG, or BMP formats.
  * 🛠️ **Customizable UI** : Includes a clear button, about dialog, and shortcut keys for efficient navigation.
  * ⚙️ **Multithreaded Processing** : Prevents UI freezing by generating images in the background.
  * 🎨 **Theming Support** : Customizable color scheme for improved visibility.
  * 🌐 **Social Integration** : Links to the Telegram channel and website for additional resources.



* * *

## Installation

  1. Download the `.nvda-addon` file from the releases page.
  2. Open NVDA and navigate to: `NVDA menu > Tools > Manage Add-ons`.
  3. Click **Install** , select the downloaded `.nvda-addon` file, and follow the prompts.
  4. Restart NVDA to enable the add-on.



* * *

## Usage

### 🔓 Open the Add-on:

  * **Shortcut** : `NVDA+Shift+A`
  * Or via `NVDA Menu > Tools > AI Image Generator`



### 🎨 Generate an Image:

  1. Enter a descriptive prompt (e.g., _"A serene mountain landscape at sunset"_).
  2. Press `Alt+G` or click the **Generate Image** button.
  3. Wait while the image is generated (processing dialog will appear).



### 💾 View and Save Image:

  * Once generated, the image is shown in a preview dialog.
  * Press `Alt+D` or click **Download Image** to save it.



### ℹ️ About Dialog:

  * Press `Alt+A` or click **About** to view version info and get social links.



### 🧹 Clear Input:

  * Press `Alt+R` or click **Clear** to reset inputs and clear preview.



### ❌ Close:

  * Press `Alt+C` or click **Close** to exit the dialog.



* * *

## Shortcut Keys

| Action | Shortcut Key | |----------------------|-------------------| | Open Generator | `NVDA+Shift+A` | | Generate Image | `Alt+G` | | Clear Input | `Alt+R` | | About Dialog | `Alt+A` | | Close Dialog | `Alt+C` | | Download Image | `Alt+D` | | Join Telegram | `Alt+J` _(About)_ | | Visit Website | `Alt+W` _(About)_ |

* * *

## Dependencies

  * **NVDA** : Version 2023.1 or later



### 🐍 Python Libraries:

  * `wx` — GUI components
  * `requests` — API communication
  * `threading`, `json`, `io`, `webbrowser` — Standard libraries
  * `concurrent.futures` — For multithreaded processing



### 🧩 NVDA Modules:

  * `gui`, `ui`, `globalPluginHandler`, `addonHandler`, `inputCore`, `scriptHandler`



* * *

## API Usage

This add-on uses the **Pollinations AI API** :  
👉 [`https://image.pollinations.ai/prompt/`](https://image.pollinations.ai/prompt/)

> **Note** : An active internet connection is required for image generation.

* * *

## Development

  * 👨‍💻 **Developer** : Sujan Rai, Team of Tech Visionary 
  * 📦 **Version** : 0.23 
  * 📝 **License** : GNU General Public License v3.0 
  * 🧑‍💻 **Source Code** : [GitHub Repository](https://github.com/techvisionaryteam/ai-image-generator-nvda-addon/)



* * *

## Contributing

Contributions are welcome!

  * Submit issues or pull requests via GitHub.
  * For major changes, contact the developer via the Telegram channel.



* * *

## Support

  * 💬 **Telegram** : Join the **Tech Visionary** Telegram channel for help and updates.
  * 🌐 **Website** : Visit **Tech Visionary Tutorials** for more tools and guides.
  * 🐞 **Issues** : Use the GitHub **Issues** tab to report bugs or request features.



* * *

## Known Issues

  * Image generation might fail if:
  * The API is down
  * The prompt is invalid
  * Supports only PNG, JPEG, and BMP formats.
  * Internet connection is mandatory.



* * *

## Changelog

### v0.24 (Initial Release)
added support to nvda v2025.1.

* * *

## Acknowledgments

  * 🙏 Thanks to the **NVDA community** for feedback and support.
  * 💡 Special thanks to **Team of Tech Visionary** for ideas and resources.
