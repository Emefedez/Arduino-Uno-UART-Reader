#include <Arduino.h>
#include <SoftwareSerial.h>

const int TX = 3; // Transmit
const int RX = 2; // Receive

SoftwareSerial myserial(RX, TX);

// Pin monitoring configuration
bool monitorDigital[14] = {false};
bool monitorAnalog[6] = {false};
unsigned long lastReportTime = 0;
const long reportInterval = 100; // ms

void setup() {
	Serial.begin(9600);
	while (!Serial) {
		; // wait for serial port to connect. Needed for native USB port only
	}

	// initialize serial communications at 9600 bps:
	myserial.begin(9600);

	Serial.println("Lectura de serial en 9600bps: ");
}

void handleConfig(String cmd) {
	// Expected format: CFG:D2=1,D3=0,A0=1...
	// Remove "CFG:"
	cmd = cmd.substring(4);

	int startIndex = 0;
	while (startIndex < cmd.length()) {
		int commaIndex = cmd.indexOf(',', startIndex);
		if (commaIndex == -1)
			commaIndex = cmd.length();

		String pair = cmd.substring(startIndex, commaIndex);
		int eqIndex = pair.indexOf('=');
		if (eqIndex != -1) {
			String pin = pair.substring(0, eqIndex);
			int val = pair.substring(eqIndex + 1).toInt();

			if (pin.startsWith("D")) {
				int p = pin.substring(1).toInt();
				if (p >= 0 && p < 14)
					monitorDigital[p] = (val == 1);
			} else if (pin.startsWith("A")) {
				int p = pin.substring(1).toInt();
				if (p >= 0 && p < 6)
					monitorAnalog[p] = (val == 1);
			}
		}
		startIndex = commaIndex + 1;
	}
	Serial.println("CONFIG_UPDATED");
}

void reportStatus() {
	String status = "STATUS:";
	bool hasData = false;

	for (int i = 0; i < 14; i++) {
		if (monitorDigital[i]) {
			if (hasData)
				status += ",";
			status += "D" + String(i) + ":" + String(digitalRead(i));
			hasData = true;
		}
	}

	for (int i = 0; i < 6; i++) {
		if (monitorAnalog[i]) {
			if (hasData)
				status += ",";
			status += "A" + String(i) + ":" + String(analogRead(i));
			hasData = true;
		}
	}

	if (hasData) {
		Serial.println(status);
	}
}

void loop() {
	// 1. Handle Serial Input (PC -> Arduino)
	if (Serial.available()) {
		String input = Serial.readStringUntil('\n');
		input.trim(); // Remove \r\n

		if (input.startsWith("CFG:")) {
			handleConfig(input);
		} else if (input.length() > 0) {
			// Original bridge logic
			Serial.println("");
			Serial.print("<- ");
			Serial.print(input);
			Serial.println("");
			myserial.print(input);
		}
	}

	// 2. Handle SoftwareSerial Input (Device -> Arduino -> PC)
	myserial.listen();
	while (myserial.available() > 0) {
		Serial.write(myserial.read());
	}

	// 3. Periodic Status Report
	if (millis() - lastReportTime > reportInterval) {
		reportStatus();
		lastReportTime = millis();
	}
}