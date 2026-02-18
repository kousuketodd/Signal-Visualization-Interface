# Automated Structural Health Monitoring & Robotic Stress Testing Platform

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/Platform-ESP32%20%7C%20Universal%20Robot-orange)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter%20%7C%20PyQt5-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

**An industrial-grade testing suite that synchronizes robotic actuators with real-time piezoresistive sensor telemetry to detect early material failure.**

Developed during my Engineering Internship at **Universidad Autónoma de Yucatán (UADY)**.

---

## 📷 Demo
[![Demo](https://img.youtube.com/vi/p3zFuhAG53s/0.jpg)](https://youtu.be/p3zFuhAG53s)

---

## 🚀 Project Overview
This project solves the problem of manual, inconsistent material stress testing. It creates a **closed-loop automated system** where a desktop application controls a 6-axis robot arm to apply precise force while simultaneously recording high-speed sensor data.

The system decouples data ingestion from visualization using multi-threading, ensuring that heavy CSV logging (O(1) circular buffers) never freezes the UI.

## ⚡ Key Features

### 🤖 Robotic Automation (Control Plane)
- **Universal Robot Integration:** Uses `urx` and TCP/IP (Port 30002) to control UR-Series robot arms.
- **Automated Cycles:** Performs "Stress-Relax" testing loops with configurable dwell times, velocity, and acceleration.
- **Safety protocols:** Immediate stop commands and joint-limit checks implemented in Python.

### 📊 Real-Time Visualization (Data Plane)
- **High-Speed Plotting:** Renders live sensor waveforms and 2D heatmaps using `CustomTkinter` and `Matplotlib`.
- **Non-Blocking Architecture:** Separation of concerns between the **Serial Worker Thread** (Data Acquisition) and the **Main GUI Thread** (Rendering).
- **Serial Command Interface:** Custom ASCII-based protocol to configure ESP32 sampling rates and states on the fly.

### 💾 Optimization
- **Circular Buffering:** Implemented O(1) fixed-size buffers for telemetry storage, preventing memory bloat during long tests.
- **Thread-Safe Logging:** Asynchronous writing to CSV files for post-process analysis in MATLAB/Excel.

---

## 🛠️ System Architecture
1.  **Host Application (Python):** The brain of the operation. Runs the GUI, manages the robot connection (Ethernet), and talks to the sensors (USB-UART).
2.  **Actuator (Universal Robot):** Receives motion commands via TCP/IP.
3.  **Sensor Node (ESP32):** Runs MicroPython firmware to sample piezoresistive arrays and stream packets to the Host.

---

## 💻 Tech Stack
* **Language:** Python 3.9+
* **GUI Libraries:** `CustomTkinter` (Dashboard), `PyQt5` (Robot Control Panel)
* **Robotics:** `urx` (Universal Robot Python Library)
* **Communication:** `pyserial` (UART), `socket` (TCP/IP)
* **Data Handling:** `numpy`, `pandas`
