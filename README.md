# Dali
### Portrait-drawing robotic arm

[![Demo](https://i.ytimg.com/vi/iyKnJWMpbK8/0.jpg)](https://youtu.be/iyKnJWMpbK8)

[Demo on YouTube](https://youtu.be/iyKnJWMpbK8)

- Takes photo with a webcam, finds edges (OpenCV - Canny detection), vectorises into contours (proprietary algorithm), converts virtual coordinates into arm's angles - implemented in Python.
- Control is via a Finite State Machine - implemented in LabView.
- DAQ: sensors - potentiometers, measuring angle deflection; switches for tracking pen levelling. PWM for adjusting motors speed, based on current action.

Created during Engineering Experience 3 at GroupT.
