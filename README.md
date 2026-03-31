# MyKilnBuddy 🚧 Work in Progress

MyKilnBuddy is a software, with which you can monitor your analog pottery firing kiln display and read the temperature values on your mobile device.

---

## Features / Architekture
- A software, that runs on an edge device (e.g. RaspberryPi3) with a webcam [v1.0]
- An API, that runs on a webserver, receiving the temperature readings and allowing for retrival [v1.0]
- A mobile app (android), with which you can read your temperature in real time (without the need to go see your kiln in person) [v1.0]

---

## Installation of Edge_Service (on the device, that gets the pictures of your kiln display)
Pull code via git:
```git clone https://github.com/MartinRuchti/MyKilnBuddy```

Create virtual environment
```
```

Activate virtual environment
```source venv/bin/activate```

install dependencies:
```sudo apt install guvcview``` (this installs guvcview in the system)
```pip install requests``` (this installs python-requests in the virtual environment)

---

## Installation of Mobile App (where you receive your data)
Pull code via git:
```git clone https://github.com/MartinRuchti/MyKilnBuddy```

Open project in AndroidStudio, build and deploy via usb, wifi, or compile an apk.

---

## Installation of Server Service
I used supabase for my service, but you can certainly use other services. 
For supabase, you create your initial tables via the sql code. Then, you create an edge service, pasting the content of the index.ts file. This will set up the TypeScript service.
After that, create a key named 'DATAPOINTS_API_KEY' in the secrets tab of your edge-function on supabase. That's it.

---

## Usage of Edge_Service
Activate virtual environment:
```source venv/bin/activate```

Run the display observer, that sends the data to the server:
```python3 <your-directory-to-the-code>/MyKilnBuddy/edge_service/kiln_observer.py \
-u "your-api-url" \
-t your-timeinterval-between-data-points-in-milliseconds \
-a1 "your-anon-key" \
-a2 "your-x-api-key" \```

You can also add -v to activate verbose mode. Also, you can add the command to your startup in ```startup.sh```.

## Usage of Mobile App
Open the app. On the first start, change to the 'configuration' page and enter your credentials (url, anon-key, x-api-key), safe, you are good to go.

---

## Technology

- Edge: Python based
- Webserver: Supabase  
- Mobile: Android app, based on java

---

## License

MIT License

---

## Contact

Martin Ruchti / GitHub: MartinRuchti
info@martin-ruchti.com