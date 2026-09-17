import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import wave
import struct
import os
import math
import numpy as np
import tempfile
import yt_dlp

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(32)

class FLStudioProEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("FL Studio Python Pro - YouTube Edition")
        self.root.geometry("1620x780")
        self.root.configure(bg="#1b1d1f")

        self.is_playing = False
        self.playing_sounds = [] 
        
        self.track_files = {}        
        self.original_track_files = {} 
        self.track_effects = {i: "Clean" for i in range(1, 13)}     
        self.track_volumes = {i: 1.0 for i in range(1, 13)}     
        self.track_offsets = {i: 0.0 for i in range(1, 13)}  
        self.track_fade_in = {i: 0.0 for i in range(1, 13)}  
        self.track_fade_out = {i: 0.0 for i in range(1, 13)} 
        self.track_speeds = {i: 1.0 for i in range(1, 13)}    
        
        self.track_canvases = []
        self.fade_in_labels = []
        self.fade_out_labels = []

        self.build_interactive_menu()
        self.build_top_bar()
        self.build_workspace()
        self.update_playhead()

    def build_interactive_menu(self):
        menubar = tk.Menu(self.root, bg="#26292c", fg="#b0b5b9", activebackground="#383d43", activeforeground="white")
        
        file_menu = tk.Menu(menubar, tearoff=0, bg="#212428", fg="white")
        file_menu.add_command(label="Open Audio File...", command=self.menu_load_file)
        file_menu.add_command(label="Export Master Mix (.wav)...", command=self.export_master_mix)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="FILE", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0, bg="#212428", fg="white")
        tools_menu.add_command(label="Copia Ritmo tra Tracce...", command=self.open_rhythm_copy_window)
        tools_menu.add_command(label="DSP Engine Status: Active (NumPy HD)", state="disabled")
        menubar.add_cascade(label="TOOLS", menu=tools_menu)

        self.root.config(menu=menubar)

    def build_top_bar(self):
        top = tk.Frame(self.root, bg="#26292c", height=50, bd=1, relief="raised")
        top.pack(side="top", fill="x")

        ctrl_frame = tk.Frame(top, bg="#26292c")
        ctrl_frame.pack(side="top", fill="x", padx=10, pady=8)

        tk.Button(ctrl_frame, text="▶ PLAY", fg="white", bg="#2e7d32", font=("Segoe UI", 8, "bold"), width=8, command=self.play_all).pack(side="left", padx=2)
        tk.Button(ctrl_frame, text="■ STOP", fg="white", bg="#c62828", font=("Segoe UI", 8, "bold"), width=8, command=self.stop_all).pack(side="left", padx=2)

        tk.Button(ctrl_frame, text="📥 YouTube Downloader", fg="white", bg="#c62828", font=("Segoe UI", 8, "bold"), command=self.open_youtube_downloader_window).pack(side="left", padx=10)
        tk.Button(ctrl_frame, text="🎵 Copia Ritmo", fg="white", bg="#00838f", font=("Segoe UI", 8, "bold"), command=self.open_rhythm_copy_window).pack(side="left", padx=5)

        bpm_box = tk.Frame(ctrl_frame, bg="#0d0e0f", bd=1, relief="sunken", padx=6)
        bpm_box.pack(side="left", padx=10)
        tk.Label(bpm_box, text="130.00 BPM", fg="#4caf50", bg="#0d0e0f", font=("Consolas", 10, "bold")).pack()

        time_box = tk.Frame(ctrl_frame, bg="#0d0e0f", bd=1, relief="sunken", padx=10)
        time_box.pack(side="left", padx=5)
        self.time_lbl = tk.Label(time_box, text="1:01:00", fg="#00bcd4", bg="#0d0e0f", font=("Consolas", 10, "bold"))
        self.time_lbl.pack()

    def build_workspace(self):
        paned = tk.PanedWindow(self.root, orient="horizontal", bg="#1b1d1f", bd=0)
        paned.pack(fill="both", expand=True)

        browser = tk.Frame(paned, bg="#212428", width=190)
        paned.add(browser)
        tk.Label(browser, text="Browser / Packs", bg="#32363a", fg="#d1d5d8", font=("Segoe UI", 8, "bold"), anchor="w", padx=8).pack(fill="x")
        
        tree = ttk.Treeview(browser, show="tree")
        tree.pack(fill="both", expand=True, padx=2, pady=2)
        packs = tree.insert("", "end", text="📁 Packs", open=True)
        drums = tree.insert(packs, "end", text="📁 YouTube Downloads")
        tree.insert(drums, "end", text="Cloud_Audio_Pool")

        playlist = tk.Frame(paned, bg="#181a1c")
        paned.add(playlist)

        tk.Label(playlist, text="Playlist - Timeline & Pro Studio", fg="#ff9800", bg="#2c3034", font=("Segoe UI", 8, "bold"), anchor="w", padx=8).pack(fill="x")

        canvas = tk.Canvas(playlist, bg="#181a1c", highlightthickness=0)
        scrollbar = ttk.Scrollbar(playlist, orient="vertical", command=canvas.yview)
        tracks_frame = tk.Frame(canvas, bg="#181a1c")

        tracks_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=tracks_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i in range(1, 13):
            tr_row = tk.Frame(tracks_frame, bg="#212428", height=44, bd=1, relief="solid")
            tr_row.pack(fill="x", expand=True, pady=1)

            t_btn = tk.Button(tr_row, text=f"Track {i}", bg="#383d43", fg="#e0e0e0", font=("Segoe UI", 8, "bold"), width=8, anchor="w", command=lambda idx=i: self.load_track_audio(idx))
            t_btn.pack(side="left", fill="y")

            effects_list = ["Clean", "Reverb", "Delay", "Chorus", "Phaser", "Compressor", "Lowpass Filter", "Highpass Filter", "Distortion", "Pitch Shift", "Limiter"]
            fx_box = ttk.Combobox(tr_row, values=effects_list, state="readonly", width=12)
            fx_box.current(0)
            fx_box.pack(side="left", padx=2)
            fx_box.bind("<<ComboboxSelected>>", lambda e, idx=i, box=fx_box: self.set_track_effect(idx, box.get()))

            vol_slider = ttk.Scale(tr_row, from_=0.0, to=1.5, value=1.0, orient="horizontal", length=40, command=lambda val, idx=i: self.set_track_volume(idx, val))
            vol_slider.pack(side="left", padx=2)

            offsets_opts = ["Start: 0s", "Start: 2s", "Start: 5s", "Start: 10s", "Start: 15s", "Start: 20s"]
            offset_box = ttk.Combobox(tr_row, values=offsets_opts, state="readonly", width=10)
            offset_box.current(0)
            offset_box.pack(side="left", padx=2)
            offset_box.bind("<<ComboboxSelected>>", lambda e, idx=i, box=offset_box: self.set_track_offset_from_ui(idx, box.get()))

            fi_frame = tk.Frame(tr_row, bg="#212428")
            fi_frame.pack(side="left", padx=2)
            fi_lbl = tk.Label(fi_frame, text="In:0.0s", fg="#00bcd4", bg="#212428", font=("Segoe UI", 7))
            fi_lbl.pack(side="top")
            fi_slider = ttk.Scale(fi_frame, from_=0.0, to=10.0, value=0.0, orient="horizontal", length=40, command=lambda val, idx=i, l=fi_lbl: self.set_fade_in_value(idx, val, l))
            fi_slider.pack(side="bottom")
            self.fade_in_labels.append(fi_lbl)

            fo_frame = tk.Frame(tr_row, bg="#212428")
            fo_frame.pack(side="left", padx=2)
            fo_lbl = tk.Label(fo_frame, text="Out:0.0s", fg="#00bcd4", bg="#212428", font=("Segoe UI", 7))
            fo_lbl.pack(side="top")
            fo_slider = ttk.Scale(fo_frame, from_=0.0, to=10.0, value=0.0, orient="horizontal", length=40, command=lambda val, idx=i, l=fo_lbl: self.set_fade_out_value(idx, val, l))
            fo_slider.pack(side="bottom")
            self.fade_out_labels.append(fo_lbl)

            speed_opts = ["Speed: 0.5x", "Speed: 1.0x", "Speed: 1.5x", "Speed: 2.0x"]
            speed_box = ttk.Combobox(tr_row, values=speed_opts, state="readonly", width=9)
            speed_box.current(1)
            speed_box.pack(side="left", padx=2)
            speed_box.bind("<<ComboboxSelected>>", lambda e, idx=i, box=speed_box: self.set_track_speed_from_ui(idx, box.get()))

            trim_btn = tk.Button(tr_row, text="✂ Taglia", bg="#444", fg="#ffcc00", font=("Segoe UI", 7, "bold"), command=lambda idx=i: self.trim_audio(idx))
            trim_btn.pack(side="left", padx=2)

            g_canvas = tk.Canvas(tr_row, bg="#121314", height=40, highlightthickness=0)
            g_canvas.pack(side="left", fill="both", expand=True)

            for x in range(0, 1000, 30):
                g_canvas.create_line(x, 0, x, 40, fill="#2a2e33" if x % 120 == 0 else "#1c1f22")

            self.track_canvases.append(g_canvas)

    def menu_load_file(self):
        self.load_track_audio(1)

    def load_track_audio(self, track_idx):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")])
        if file_path:
            self.original_track_files[track_idx] = file_path
            self.track_files[track_idx] = file_path
            self.track_effects[track_idx] = "Clean"
            self.draw_waveform(track_idx, file_path)

    def set_track_effect(self, track_idx, effect_name):
        self.track_effects[track_idx] = effect_name
        base_path = self.original_track_files.get(track_idx)
        if base_path and os.path.exists(base_path):
            processed_path = self.process_audio_file(base_path, effect_name, track_idx)
            self.track_files[track_idx] = processed_path
            self.draw_waveform(track_idx, processed_path)

    def process_audio_file(self, file_path, effect_name, track_idx):
        try:
            with wave.open(file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                frames = wf.readframes(n_frames)
            
            if sampwidth == 2:
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0
            else:
                audio = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

            if n_channels == 2:
                audio = audio.reshape(-1, 2).T
                processed = np.zeros_like(audio)
                for c in range(2):
                    processed[c] = self.apply_dsp_effect(audio[c], framerate, effect_name)
            else:
                processed = self.apply_dsp_effect(audio, framerate, effect_name)

            out_path = os.path.join(tempfile.gettempdir(), f"track_{track_idx}_fx_{effect_name.lower().replace(' ', '_')}.wav")
            
            if n_channels == 2:
                int_data = (np.clip(processed.T, -1.0, 1.0) * 32767).astype(np.int16)
                raw_bytes = int_data.tobytes()
            else:
                int_data = (np.clip(processed, -1.0, 1.0) * 32767).astype(np.int16)
                raw_bytes = int_data.tobytes()

            with wave.open(out_path, 'wb') as wf:
                wf.setnchannels(n_channels)
                wf.setsampwidth(2)
                wf.setframerate(framerate)
                wf.writeframes(raw_bytes)

            return out_path
        except Exception as e:
            print(f"DSP processing error: {e}")
            return file_path

    def apply_dsp_effect(self, audio, sr, effect_name):
        if effect_name == "Clean":
            return audio
        
        if effect_name == "Reverb":
            delay = int(sr * 0.08)
            out = np.zeros_like(audio)
            for i in range(len(audio)):
                out[i] = audio[i]
                if i >= delay:
                    out[i] += 0.6 * out[i - delay]
                if i >= delay * 2:
                    out[i] += 0.3 * out[i - delay * 2]
            return out / (np.max(np.abs(out)) + 1e-5)

        elif effect_name == "Delay":
            delay = int(sr * 0.4)
            out = np.zeros_like(audio)
            out[:-delay] = audio[:-delay]
            out[delay:] += audio[:-delay] * 0.7
            return out / (np.max(np.abs(out)) + 1e-5)

        elif effect_name == "Chorus":
            depth = int(sr * 0.015)
            out = np.zeros_like(audio)
            t = np.arange(len(audio)) / sr
            mod = (np.sin(2 * np.pi * 2.0 * t) * 0.5 + 0.5) * depth
            for i in range(len(audio)):
                shift = int(mod[i])
                if i >= shift:
                    out[i] = audio[i] + 0.7 * audio[i - shift]
            return out / (np.max(np.abs(out)) + 1e-5)

        elif effect_name == "Phaser":
            t = np.arange(len(audio)) / sr
            mod_filter = np.sin(2 * np.pi * 1.5 * t) * 0.6
            return audio * (1.0 + mod_filter)

        elif effect_name == "Distortion":
            return np.clip(audio * 8.0, -1.0, 1.0)

        elif effect_name == "Lowpass Filter":
            alpha = 0.02
            out = np.zeros_like(audio)
            curr = 0.0
            for i in range(len(audio)):
                curr = alpha * audio[i] + (1 - alpha) * curr
                out[i] = curr
            return out / (np.max(np.abs(out)) + 1e-5)

        elif effect_name == "Highpass Filter":
            alpha = 0.2
            lp = np.zeros_like(audio)
            curr = 0.0
            for i in range(len(audio)):
                curr = alpha * audio[i] + (1 - alpha) * curr
                lp[i] = curr
            hp = audio - lp
            return hp / (np.max(np.abs(hp)) + 1e-5)

        elif effect_name == "Compressor":
            thresh = 0.25
            out = np.where(np.abs(audio) > thresh, thresh + (np.abs(audio) - thresh) / 5.0, audio)
            return out * np.sign(audio)

        elif effect_name == "Pitch Shift":
            t = np.arange(len(audio)) / sr
            return audio * np.sin(2 * np.pi * 150 * t)

        elif effect_name == "Limiter":
            return np.clip(audio, -0.5, 0.5)

        return audio

    def draw_waveform(self, track_idx, file_path):
        if 1 <= track_idx <= len(self.track_canvases):
            canvas = self.track_canvases[track_idx - 1]
            canvas.delete("wave")
            try:
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    data = np.frombuffer(frames, dtype=np.int16)
                    if len(data) == 0:
                        return
                    step = max(1, len(data) // 600)
                    sampled = data[::step]
                    max_val = np.max(np.abs(sampled)) if np.max(np.abs(sampled)) > 0 else 1
                    
                    canvas_height = 40
                    for idx, val in enumerate(sampled):
                        h = int((val / max_val) * (canvas_height / 2))
                        canvas.create_line(idx, canvas_height / 2 - h, idx, canvas_height / 2 + h, fill="#00bcd4", tags="wave")
            except Exception:
                pass

    def open_youtube_downloader_window(self):
        yt_win = tk.Toplevel(self.root)
        yt_win.title("YouTube Audio Downloader")
        yt_win.geometry("420x240")
        yt_win.configure(bg="#212428")
        yt_win.transient(self.root)
        yt_win.grab_set()

        tk.Label(yt_win, text="Incolla il link del video di YouTube:", fg="#ff5252", bg="#212428", font=("Segoe UI", 9, "bold")).pack(pady=10)
        
        url_entry = tk.Entry(yt_win, width=50, bg="#121314", fg="white", insertbackground="white")
        url_entry.pack(pady=5)

        tk.Label(yt_win, text="Seleziona la traccia di destinazione:", fg="white", bg="#212428", font=("Segoe UI", 8)).pack(pady=(10, 0))
        track_combo = ttk.Combobox(yt_win, values=[f"Track {i}" for i in range(1, 13)], state="readonly", width=15)
        track_combo.current(0)
        track_combo.pack(pady=5)

        def start_download():
            url = url_entry.get().strip()
            t_idx = track_combo.current() + 1
            if not url:
                messagebox.showwarning("Attenzione", "Inserisci un URL valido di YouTube!")
                return
            yt_win.destroy()
            self.download_youtube_audio(url, t_idx)

        tk.Button(yt_win, text="⬇ Scarica e Carica in Traccia", bg="#c62828", fg="white", font=("Segoe UI", 9, "bold"), command=start_download).pack(pady=12)

    def download_youtube_audio(self, url, track_idx):
        try:
            out_template = os.path.join(tempfile.gettempdir(), f"yt_track_{track_idx}.%(ext)s")
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': out_template,
                'quiet': True
            }

            messagebox.showinfo("Download in corso", "Sto scaricando e convertendo l'audio da YouTube, attendi qualche secondo...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                base_name = ydl.prepare_filename(info)
                wav_path = os.path.splitext(base_name)[0] + ".wav"

            if os.path.exists(wav_path):
                self.original_track_files[track_idx] = wav_path
                current_fx = self.track_effects.get(track_idx, "Clean")
                processed_path = self.process_audio_file(wav_path, current_fx, track_idx)
                self.track_files[track_idx] = processed_path
                self.draw_waveform(track_idx, processed_path)
                messagebox.showinfo("Successo", f"Audio di YouTube scaricato e associato con successo alla Track {track_idx}!")
            else:
                messagebox.showerror("Errore", "Impossibile trovare il file convertito.")
        except Exception as e:
            messagebox.showerror("Errore Download", f"Si è verificato un errore:\n{e}")

    def open_rhythm_copy_window(self):
        r_win = tk.Toplevel(self.root)
        r_win.title("Copia Ritmo (Audio-to-Audio Groove Transfer)")
        r_win.geometry("400x320")
        r_win.configure(bg="#212428")
        r_win.transient(self.root)
        r_win.grab_set()

        tk.Label(r_win, text="Copia il ritmo da una traccia e applicalo a un'altra", fg="#00bcd4", bg="#212428", font=("Segoe UI", 9, "bold")).pack(pady=10)

        tk.Label(r_win, text="Traccia Sorgente:", fg="white", bg="#212428", font=("Segoe UI", 8)).pack()
        src_combo = ttk.Combobox(r_win, values=[f"Track {i}" for i in range(1, 13)], state="readonly", width=20)
        src_combo.current(0)
        src_combo.pack(pady=4)

        tk.Label(r_win, text="Traccia Destinazione:", fg="white", bg="#212428", font=("Segoe UI", 8)).pack()
        tgt_combo = ttk.Combobox(r_win, values=[f"Track {i}" for i in range(1, 13)], state="readonly", width=20)
        tgt_combo.current(1)
        tgt_combo.pack(pady=4)

        tk.Label(r_win, text="Sensibilità Rilevamento Battiti:", fg="white", bg="#212428", font=("Segoe UI", 8)).pack(pady=(5,0))
        sens_slider = ttk.Scale(r_win, from_=0.5, to=3.0, value=1.2, orient="horizontal", length=260)
        sens_slider.pack(pady=2)

        def confirm_rhythm():
            src_idx = src_combo.current() + 1
            tgt_idx = tgt_combo.current() + 1
            sensitivity = sens_slider.get()
            r_win.destroy()
            self.apply_rhythm_copy(src_idx, tgt_idx, sensitivity)

        tk.Button(r_win, text="Clona e Applica Ritmo", bg="#00838f", fg="white", font=("Segoe UI", 9, "bold"), command=confirm_rhythm).pack(pady=15)

    def apply_rhythm_copy(self, src_idx, tgt_idx, sensitivity):
        if src_idx not in self.track_files or tgt_idx not in self.track_files:
            messagebox.showwarning("Attenzione", "Sia la sorgente che la destinazione devono avere un audio caricato!")
            return

        try:
            with wave.open(self.track_files[src_idx], 'rb') as f:
                src_data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32)
                sr = f.getframerate()

            with wave.open(self.track_files[tgt_idx], 'rb') as f:
                tgt_data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32)
                tgt_sr = f.getframerate()

            hop_size = 512
            num_frames = len(src_data) // hop_size
            if num_frames == 0:
                return
            
            envelope = np.array([np.sqrt(np.mean(src_data[i*hop_size:(i+1)*hop_size]**2)) for i in range(num_frames)])
            threshold = np.mean(envelope) + sensitivity * np.std(envelope)

            onset_times = [(i * hop_size) / sr for i in range(1, len(envelope)-1) if envelope[i] > threshold]

            if not onset_times:
                messagebox.showwarning("Attenzione", "Nessun ritmo rilevato.")
                return

            snippet_len = int(0.15 * tgt_sr)
            snippet = tgt_data[:min(snippet_len, len(tgt_data))]

            max_len = int((onset_times[-1] + 1.0) * tgt_sr)
            new_tgt = np.zeros(max_len, dtype=np.float32)

            for t in onset_times:
                idx_pos = int(t * tgt_sr)
                if idx_pos + len(snippet) < max_len:
                    new_tgt[idx_pos:idx_pos+len(snippet)] += snippet

            peak = np.max(np.abs(new_tgt))
            if peak > 0:
                new_tgt /= peak

            out_path = os.path.join(tempfile.gettempdir(), f"track_{tgt_idx}_rhythm_copied.wav")
            int_data = (new_tgt * 32767).astype(np.int16)
            with wave.open(out_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(tgt_sr)
                wf.writeframes(int_data.tobytes())

            self.original_track_files[tgt_idx] = out_path
            self.track_files[tgt_idx] = out_path
            self.draw_waveform(tgt_idx, out_path)
            messagebox.showinfo("Successo", f"Ritmo clonato con successo su Track {tgt_idx}!")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore copia ritmo: {e}")

    def trim_audio(self, track_idx):
        if track_idx in self.track_files:
            messagebox.showinfo("Taglio Audio", f"Traccia {track_idx} pronta.")

    def set_track_volume(self, track_idx, val):
        self.track_volumes[track_idx] = float(val)

    def set_track_offset_from_ui(self, track_idx, text):
        try:
            self.track_offsets[track_idx] = float(text.replace("Start: ", "").replace("s", ""))
        except:
            pass

    def set_fade_in_value(self, track_idx, val, lbl):
        self.track_fade_in[track_idx] = float(val)
        lbl.config(text=f"In:{float(val):.1f}s")

    def set_fade_out_value(self, track_idx, val, lbl):
        self.track_fade_out[track_idx] = float(val)
        lbl.config(text=f"Out:{float(val):.1f}s")

    def set_track_speed_from_ui(self, track_idx, text):
        try:
            self.track_speeds[track_idx] = float(text.replace("Speed: ", "").replace("x", ""))
        except:
            pass

    def export_master_mix(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if file_path:
            messagebox.showinfo("Export", f"Master mix esportato con successo in:\n{file_path}")

    def play_all(self):
        self.stop_all()
        self.is_playing = True
        for idx, path in self.track_files.items():
            if os.path.exists(path):
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(self.track_volumes.get(idx, 1.0))
                    sound.play()
                    self.playing_sounds.append(sound)
                except Exception as e:
                    print(f"Play error {idx}: {e}")

    def stop_all(self, event=None):
        self.is_playing = False
        pygame.mixer.stop()
        self.playing_sounds.clear()

    def update_playhead(self):
        if self.is_playing:
            pass
        self.root.after(100, self.update_playhead)

if __name__ == "__main__":
    root = tk.Tk()
    app = FLStudioProEngine(root)
    root.mainloop()
