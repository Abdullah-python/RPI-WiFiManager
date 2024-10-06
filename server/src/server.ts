import express, { NextFunction, Request, Response } from 'express';
import path from 'path';
import fs from 'fs/promises';
const cors = require('cors'); // Import the cors package


////////////////////////////// Setup ///////////////////////////////////////////

const HOST_NAME = 'wolfpak.portal';
const FRONTEND_FOLDER = path.join(__dirname, '../', 'public');

const app = express();

app.use(express.json());

const corsOptions = {
    origin: '*', // Temporarily allow all origins for debugging
    methods: 'GET, POST, PUT, DELETE, OPTIONS',
    allowedHeaders: 'Content-Type, Authorization',
};

app.use(cors(corsOptions));

app.options('/wifi-config', cors()); // Handle preflight requests


// Redirect every request to our application
// https://raspberrypi.stackexchange.com/a/100118
// [You need a self-signed certificate if you really want 
// an https connection. In my experience, this is just a pain to do
// and probably overkill for a project where you have your own WiFi network
// without Internet access anyway.]
app.use((req: Request, res: Response, next: NextFunction) => {
    // Allow localhost or local IP addresses to bypass the hostname check
    if (req.hostname !== HOST_NAME && req.hostname !== 'localhost' && req.hostname !== '127.0.0.1' && req.hostname !== '192.168.4.1') {
        return res.redirect(`http://${HOST_NAME}`);
    }
    next();
});

/////////////////////////////// Endpoints //////////////////////////////////////

// Serve frontend
app.get('/', (req, res, next) => {
    res.sendFile(path.join(FRONTEND_FOLDER, 'index.html'));
});

app.post('/wifi-config', async (req, res) => {    
    const data = req.body;
    console.log('Received data:', data);
    
    try {
        await fs.writeFile('/home/abdullah/credentials.txt', JSON.stringify(data, null, 2));
        console.log('Data saved successfully');
        res.send('Saved');
    } catch (err) {
        console.error('Error writing file:', err);
        res.status(500).send('Error in file saving data');
    }
});

app.post('/test', async (req, res) => {
    try {
        await fs.writeFile('/home/abdullah/test.txt', 'Hello World');
        res.send('Test file written');
    } catch (err) {
        console.error('Error writing file:', err);
        res.status(500).send('Error writing test file');
    }
});

///////////////////////////// Server listening /////////////////////////////////

// Listen for requests
// If you change the port here, you have to adjust the ip tables as well
// see file: access-point/setup-access-point.sh
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Node version: ${process.version}`);
    console.log(`⚡ Raspberry Pi Server listening on port ${PORT}`);
});