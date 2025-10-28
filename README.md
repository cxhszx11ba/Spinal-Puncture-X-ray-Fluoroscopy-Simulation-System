# Spinal-Puncture-X-ray-Fluoroscopy-Simulation-System
In traditional spinal surgical simulators, after spinal puncture needle penetrates "simulated skin", "needle tip" position in simulated body is only obtainable via fluoroscopic imaging. This software works without fluoroscopic equipment; it simulates needle tip position by tracking "fiducial markers" on spinal puncture needle tail.

The specific operation videos are as follows.
https://b23.tv/vPGvnLl1.

Important Note: Simulated anteroposterior (AP) and lateral (LAT) films in this software correspond to 3D-printed models. Before using the built-in AP and lateral films, download and print the model in advance：https://makerworld.com.cn/zh/models/1517922-yao-zhui-wei-chuang-shou-zhu-he-chuan-ci-mo-ni-qi#profileId-1658428

Overview

This software is an auxiliary tool for simulating lumbar puncture procedures. It utilizes two cameras as Anteroposterior (AP) and Lateral (LAT) views, respectively. It overlays preset medical images onto the live video feeds. Users can adjust the position, scale, rotation, and transparency of the overlays to align them with the real-time scene. Once aligned, users can capture the current view and simulate the puncture trajectory by clicking points on the captured image.

2. System Requirements
- At least two cameras must be connected and available.
  
3. Operating Instructions
Step 1: Camera Selection
1. Launch the Software: Upon running the application（runme.py in the code folder）, the "Camera Selection" window will appear first.
2. Camera Detection: The window automatically detects all connected cameras and displays their live feeds.
3. Select in Order:
  - First, click on the camera feed you wish to use as the **"AP view"**.
  - Second, click on the camera feed you wish to use as the **"LAT view"**.
  - Note: The order of selection is crucial as it determines which camera corresponds to which view. A red border will appear around the selected camera feeds.
4. Enter Main Window: After selecting two cameras, the selection window will close automatically, and the main operation interface will open.
<img width="1600" height="1256" alt="image" src="https://github.com/user-attachments/assets/254f3301-2af8-4701-8566-b6d7def9ec51" />

Step 2: Adjusting the Overlay Images
1. Interface Layout: The main interface displays two live video windows at the top (left: AP view, right: LAT view) and two static image panes at the bottom for displaying captures.
2. Activate Control: To adjust an overlay image in one of the views, **you must first move your mouse cursor over that specific video window**.
3. Use Keyboard for Adjustments:
  - Position: Use the Arrow Keys (Up/Down/Left/Right) to fine-tune the overlay's position.
  - Scale: Press + (plus) to zoom in; press - (minus) to zoom out.
  - Transparency (Alpha): Press W to increase opacity; press S to decrease opacity (more transparent).
  - Rotation: Press A to rotate counter-clockwise; press D to rotate clockwise.
4. Align to Target: Adjust the images until the overlays in the AP and LAT views are precisely aligned with the key anatomical structures on the model, such as the **vertebral body, pedicle, spinous process, and transverse process**.
5. Auto-Save: This alignment process typically only needs to be completed once on the same computer, as the software will automatically save your settings for future use.
  
Step 3: Puncture and Simulation
1. Puncture and Capture: Once the overlays in both views are correctly aligned, perform the puncture procedure on the model using the **specialized puncture needle with markers**. After the puncture is complete, click the “Perspective and simulate puncture trajectory” button at the bottom to capture the images. If you need to adjust the needle's position, simply reposition the physical needle and click the button again to update the captured images.
2. Generate Perspective Views: Upon clicking, the current frames from the top two live video windows (including your adjusted overlays) will be captured and displayed in the two "perspective" panes below.
3. Begin Simulation: The software now enters trajectory simulation mode. When you move your mouse over either of the bottom perspective panes, the cursor will change to a **crosshair**.
4. Mark Trajectory Points: In each perspective pane, you need to sequentially click on the visible red, green, and blue markers on the puncture needle to define the exact trajectory. Based on the positions of these three points, the system will automatically calculate and draw the complete puncture path, clearly indicating the location of the **needle tip**.
  
4. Exiting the Application
Simply close the main window. The software will automatically release the cameras and save the current overlay settings.
