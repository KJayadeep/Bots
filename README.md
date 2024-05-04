This project utilizes hand gestures detected through a webcam feed to control screen-brightness and volume along with screen shot option.
The Webcam detects the distance between Thumb and index finger in real-time using the MediaPipe library and uses screen_brightness_control & pycaw libraries for brightness and volume control.
when the two thumbs and index fingers meet(intersection of green lines) a screenshot.png is generated. 
The left hand controls brightness, while the right hand controls volume.
Visual feedback is provided in real-time through the webcam feed(such as circles and lines) on detected hands,so we can make a easy screenshot .

