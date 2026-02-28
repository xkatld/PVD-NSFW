import express from 'express';
import Database from 'better-sqlite3';
import path from 'path';
import cors from 'cors';
import https from 'https';
import fs from 'fs';
import cookieParser from 'cookie-parser';
import { fileURLToPath } from 'url';

const app = express();
const port = 8443;
const PASSWORD = 'Aiwang888';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const db_path = path.join(__dirname, '../videos/data.db');
const db = new Database(db_path);

const options = {
    key: fs.readFileSync(path.join(__dirname, 'key.pem')),
    cert: fs.readFileSync(path.join(__dirname, 'cert.pem'))
};

app.use(cors());
app.use(cookieParser());
app.use(express.json());

const auth = (req: any, res: any, next: any) => {
    if (req.cookies.auth === PASSWORD) {
        next();
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
};

app.post('/api/login', (req, res) => {
    if (req.body.password === PASSWORD) {
        res.cookie('auth', PASSWORD, { maxAge: 86400 * 1000 * 30, httpOnly: true });
        res.json({ success: true });
    } else {
        res.status(403).json({ error: 'Wrong password' });
    }
});

app.use(express.static(path.join(__dirname, 'public')));
app.use('/videos', auth, express.static(path.join(__dirname, '../videos')));

app.get('/api/videos', auth, (req, res) => {
    try {
        const rows = db.prepare('SELECT id, title, labels, file_name FROM video WHERE file_name IS NOT NULL').all();
        const videos = rows.map((row: any) => ({
            id: row.id,
            title: row.title,
            labels: JSON.parse(row.labels),
            url: `/videos/${row.file_name}`
        }));
        res.json(videos);
    } catch (error) {
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

https.createServer(options, app).listen(port, () => {
    console.log(`[READY] https://localhost:${port}`);
});
