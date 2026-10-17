//! The Redrob Code app bridge: this app's tools, served to the shared Redrob Code daemon.
//!
//! `redrob-app-bridge` serves the tools over MCP on loopback and registers them with the daemon,
//! so the agent in any Redrob surface (a phone chat included) can drive the open project as
//! `app:film`. Every tool handler runs on one of the bridge's own threads; the project lives on
//! the UI thread. The handlers therefore never touch the editor: each one is a request/reply round
//! trip over the same control channel the JSON-lines control server and the built-in agent use
//! (`control_server.rs` -> [`crate::shell::ShellApp::service_control`] -> the Edit editor's
//! `drain_control`). A handler sends an `engine.execute` [`ControlRequest`], asks for a repaint
//! and blocks on the reply, which the UI thread gives between frames with the very functions the
//! menus call. Nothing here holds editor state.
//!
//! The daemon is optional: when it cannot be reached the failure is logged and the app runs
//! without the bridge.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{Receiver, Sender, channel};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use redrob_app_bridge::{AppBridge, AppBridgeConfig, Tool};
use redrob_film_time::Tick;
use redrob_film_ui_egui::ControlRequest;
use serde_json::{Value, json};

/// The name the daemon lists the tools under (`app:film`).
const APP_NAME: &str = "film";
/// How long a tool call waits for the UI thread's answer before giving up.
const REPLY_TIMEOUT: Duration = Duration::from_secs(30);
/// The folder `render` writes to when the caller names none and the project has no file yet
/// (`file.exportMedia` expands `~` and treats a trailing separator as "a folder, name the file
/// after the sequence").
const DEFAULT_RENDER_DIR: &str = "~/";

/// Join the control server's requests and the bridge's into one channel for the shell.
///
/// `control_rx` is what `control_server::start` returned; the returned receiver replaces it in
/// `ShellApp::new`, and the returned sender is what [`start`] gives the tool handlers. Every
/// request carries its own reply sender, so forwarding is a plain move. The forwarding thread ends
/// with the control server (or at once when the server never bound: its sender is already gone).
pub fn relay(control_rx: Receiver<ControlRequest>) -> (Receiver<ControlRequest>, Sender<ControlRequest>) {
    let (tx, rx) = channel::<ControlRequest>();
    let forward = tx.clone();
    let spawned = std::thread::Builder::new().name("app-bridge-relay".into()).spawn(move || {
        for req in control_rx {
            if forward.send(req).is_err() {
                return;
            }
        }
    });
    if let Err(e) = spawned {
        log::warn!("app bridge: could not start the control relay thread: {e}");
    }
    (rx, tx)
}

/// The bridge as the shell holds it: filled in by the start-up thread once the daemon answered,
/// emptied by [`BridgeHandle::stop`] on exit.
#[derive(Default)]
pub struct BridgeHandle {
    bridge: Arc<Mutex<Option<AppBridge>>>,
    stopped: Arc<AtomicBool>,
}

impl BridgeHandle {
    /// Unregister from the daemon and stop serving. A bridge that is still starting is dropped
    /// (which unregisters it) as soon as its start returns.
    pub fn stop(&self) {
        self.stopped.store(true, Ordering::SeqCst);
        let mut slot = self.bridge.lock().unwrap_or_else(|e| e.into_inner());
        if let Some(bridge) = slot.take() {
            bridge.stop();
        }
    }
}

/// Serve the tools and register with the daemon, on a background thread: finding or starting the
/// daemon can take a moment and the window should not wait for it. When the daemon is out of reach
/// the failure is logged and the app works without the bridge.
pub fn start(tx: Sender<ControlRequest>, ctx: egui::Context) -> BridgeHandle {
    let handle = BridgeHandle::default();
    let (slot, stopped) = (handle.bridge.clone(), handle.stopped.clone());
    let link = Link { tx, ctx };
    let spawned = std::thread::Builder::new().name("app-bridge-start".into()).spawn(move || {
        let tools = tools(&link);
        let count = tools.len();
        let config = AppBridgeConfig { version: Some(env!("CARGO_PKG_VERSION").into()), ..AppBridgeConfig::new(APP_NAME, tools) };
        match AppBridge::start(config) {
            Ok(bridge) => {
                let mut guard = slot.lock().unwrap_or_else(|e| e.into_inner());
                if stopped.load(Ordering::SeqCst) {
                    // The window closed while the daemon was being found: unregister again.
                    drop(guard);
                    bridge.stop();
                    return;
                }
                log::info!("app bridge: {count} tools registered with Redrob Code as app:{APP_NAME} at {}", bridge.mcp_url());
                *guard = Some(bridge);
            }
            Err(e) => log::warn!("app bridge: Redrob Code is not reachable, the app runs without it: {e}"),
        }
    });
    if let Err(e) = spawned {
        log::warn!("app bridge: could not start its thread: {e}");
    }
    handle
}

// ----------------------------------------------------------------------------------------------
// The round trip to the UI thread
// ----------------------------------------------------------------------------------------------

/// What every handler needs: the control channel and the context to wake the UI thread with.
#[derive(Clone)]
struct Link {
    tx: Sender<ControlRequest>,
    ctx: egui::Context,
}

impl Link {
    /// Run one engine command on the UI thread (`engine.execute {command, params}`) and return
    /// its `result`; the editor's `error` text when it refused.
    fn execute(&self, command: &str, params: Value) -> Result<Value, String> {
        let (req, reply) = ControlRequest::new("engine.execute", json!({"command": command, "params": params}));
        self.tx.send(req).map_err(|_| "the editor's control channel is closed".to_string())?;
        self.ctx.request_repaint();
        let answer =
            reply.recv_timeout(REPLY_TIMEOUT).map_err(|_| format!("`{command}` got no answer from the editor within {} s", REPLY_TIMEOUT.as_secs()))?;
        if answer.get("ok").and_then(Value::as_bool) == Some(true) {
            Ok(answer.get("result").cloned().unwrap_or(Value::Null))
        } else {
            Err(answer.get("error").and_then(Value::as_str).unwrap_or("the editor refused the command").to_string())
        }
    }

    /// `sequence.inspect` of the active sequence.
    fn sequence(&self) -> Result<Value, String> {
        self.execute("sequence.inspect", json!({}))
    }
}

// ----------------------------------------------------------------------------------------------
// The tools
// ----------------------------------------------------------------------------------------------

fn tools(link: &Link) -> Vec<Tool> {
    let tool = |name: &str, description: &str, schema: Value, run: fn(&Link, &Value) -> Result<String, String>| {
        let link = link.clone();
        Tool::new(name, description, schema, move |args| run(&link, &args))
    };
    let object = |properties: Value, required: &[&str]| json!({ "type": "object", "properties": properties, "required": required });
    let seconds = |what: &str| json!({ "type": "number", "description": what });
    let clip_id = || json!({ "type": "integer", "description": "The clip id, as list_clips shows it." });
    vec![
        tool(
            "project_info",
            "Describe the open project and its active sequence: file path, duration, frame rate, resolution, track and clip counts.",
            object(json!({}), &[]),
            project_info,
        ),
        tool(
            "open_project",
            "Open a Redrob Film project file (.rfilm) in the editor and describe it.",
            object(json!({ "path": { "type": "string", "description": "Absolute path of the project file." } }), &["path"]),
            open_project,
        ),
        tool(
            "list_clips",
            "List the active sequence's clips, one per line: id, track, name, timeline in/out and source in/out in seconds.",
            object(
                json!({ "track": { "type": "string", "description": "Only this track: V1, A2, a track id or a track name. All tracks when omitted." } }),
                &[],
            ),
            list_clips,
        ),
        tool(
            "trim_clip",
            "Move a clip's in and/or out point to new timeline positions in seconds (a regular trim: neighbours stay where they are).",
            object(
                json!({
                    "id": clip_id(),
                    "start": seconds("New timeline start of the clip, in seconds."),
                    "end": seconds("New timeline end of the clip, in seconds."),
                }),
                &["id"],
            ),
            trim_clip,
        ),
        tool(
            "split_clip",
            "Cut a clip in two at a timeline position in seconds; answers the ids of the pieces.",
            object(json!({ "id": clip_id(), "at": seconds("Timeline position of the cut, in seconds.") }), &["id", "at"]),
            split_clip,
        ),
        tool(
            "set_playhead",
            "Move the playhead of the active sequence to a timeline position in seconds.",
            object(json!({ "at": seconds("Timeline position in seconds.") }), &["at"]),
            set_playhead,
        ),
        tool(
            "render",
            "Start rendering (exporting) the active sequence to a media file in the background; answers the job id and the output path. Poll render_status for progress.",
            object(
                json!({
                    "path": { "type": "string", "description": "Output file, or a folder ending in a separator (the file is named after the sequence). Defaults to the project's folder." },
                    "preset": { "type": "string", "description": "An export preset name, e.g. \"H.264 1080p\"; the format default when omitted." },
                }),
                &[],
            ),
            render,
        ),
        tool(
            "render_status",
            "Progress of a render job: percent done, time left, and the output path once it has finished (or the error).",
            object(json!({ "job_id": { "type": "integer", "description": "The job id render answered; the latest job when omitted." } }), &[]),
            render_status,
        ),
    ]
}

// ---------- arguments ----------

fn arg_str<'a>(args: &'a Value, key: &str) -> Result<&'a str, String> {
    args.get(key).and_then(Value::as_str).filter(|s| !s.trim().is_empty()).ok_or_else(|| format!("`{key}` is required"))
}

fn arg_f64(args: &Value, key: &str) -> Result<f64, String> {
    opt_f64(args, key)?.ok_or_else(|| format!("`{key}` is required"))
}

fn opt_f64(args: &Value, key: &str) -> Result<Option<f64>, String> {
    match args.get(key) {
        None | Some(Value::Null) => Ok(None),
        Some(v) => v.as_f64().filter(|f| f.is_finite()).map(Some).ok_or_else(|| format!("`{key}` must be a number of seconds")),
    }
}

fn arg_u64(args: &Value, key: &str) -> Result<u64, String> {
    opt_u64(args, key)?.ok_or_else(|| format!("`{key}` is required"))
}

fn opt_u64(args: &Value, key: &str) -> Result<Option<u64>, String> {
    match args.get(key) {
        None | Some(Value::Null) => Ok(None),
        Some(v) => v
            .as_u64()
            .or_else(|| v.as_f64().filter(|f| f.is_finite() && f.fract() == 0.0 && *f >= 0.0).map(|f| f as u64))
            .or_else(|| v.as_str().and_then(|s| s.trim().trim_start_matches('#').parse().ok()))
            .map(Some)
            .ok_or_else(|| format!("`{key}` must be a non-negative integer id")),
    }
}

// ---------- the sequence as `sequence.inspect` describes it ----------

fn ticks(v: &Value) -> Tick {
    Tick(v.as_i64().unwrap_or(0))
}

fn secs(v: &Value) -> String {
    format!("{:.3}", ticks(v).seconds())
}

/// One timeline track with its position label (`V1`, `A2`).
#[derive(Debug)]
struct TrackView<'a> {
    label: String,
    track: &'a Value,
}

impl<'a> TrackView<'a> {
    fn id(&self) -> u64 {
        self.track.get("id").and_then(Value::as_u64).unwrap_or(0)
    }
    fn name(&self) -> &'a str {
        self.track.get("name").and_then(Value::as_str).unwrap_or("")
    }
    /// The clips, borrowed from the inspection (not from this view).
    fn items(&self) -> &'a [Value] {
        self.track.get("items").and_then(Value::as_array).map(Vec::as_slice).unwrap_or(&[])
    }
    /// `V1` / `A2` / the id / the name, any case.
    fn matches(&self, want: &str) -> bool {
        let want = want.trim();
        self.label.eq_ignore_ascii_case(want) || self.name().eq_ignore_ascii_case(want) || want.parse::<u64>().is_ok_and(|id| id == self.id())
    }
}

fn tracks(seq: &Value) -> Vec<TrackView<'_>> {
    let mut all = Vec::new();
    for (key, prefix) in [("video", 'V'), ("audio", 'A')] {
        for (i, track) in seq.get(key).and_then(Value::as_array).into_iter().flatten().enumerate() {
            all.push(TrackView { label: format!("{prefix}{}", i + 1), track });
        }
    }
    all
}

/// The clip `id` and its track in `seq`.
fn find_clip<'a>(seq: &'a Value, id: u64) -> Result<(TrackView<'a>, &'a Value), String> {
    for track in tracks(seq) {
        if let Some(item) = track.items().iter().find(|i| i.get("clip").and_then(Value::as_u64) == Some(id)) {
            return Ok((track, item));
        }
    }
    Err(format!("no clip #{id} in the active sequence (list_clips shows the ids)"))
}

fn clip_line(track: &TrackView<'_>, item: &Value) -> String {
    let s = |k: &str| item.get(k).and_then(Value::as_str).unwrap_or("");
    let v = |k: &str| item.get(k).unwrap_or(&Value::Null);
    let mut line = format!(
        "#{} {} \"{}\" {}s-{}s source {}s-{}s",
        v("clip"),
        track.label,
        s("name"),
        secs(v("start")),
        secs(v("end")),
        secs(v("sourceIn")),
        secs(v("sourceOut"))
    );
    if item.get("enabled").and_then(Value::as_bool) == Some(false) {
        line.push_str(" (disabled)");
    }
    line
}

fn sequence_summary(seq: &Value) -> String {
    let settings = seq.get("settings").unwrap_or(&Value::Null);
    let fps = settings.get("frame_rate").map(|r| {
        let num = r.get("num").and_then(Value::as_f64).unwrap_or(0.0);
        let den = r.get("den").and_then(Value::as_f64).unwrap_or(1.0);
        if den == 0.0 { 0.0 } else { num / den }
    });
    let fps = fps.map(|f| format!("{f:.3}").trim_end_matches('0').trim_end_matches('.').to_string()).unwrap_or_else(|| "?".into());
    let all = tracks(seq);
    let video = all.iter().filter(|t| t.label.starts_with('V')).count();
    let audio = all.len() - video;
    let clips: usize = all.iter().map(|t| t.items().len()).sum();
    format!(
        "sequence \"{}\" (id {}): duration {} s, {} fps, {}x{}, {} video / {} audio tracks, {} clips, playhead {} s",
        seq.get("name").and_then(Value::as_str).unwrap_or(""),
        seq.get("id").unwrap_or(&Value::Null),
        secs(seq.get("duration").unwrap_or(&Value::Null)),
        fps,
        settings.get("width").unwrap_or(&Value::Null),
        settings.get("height").unwrap_or(&Value::Null),
        video,
        audio,
        clips,
        secs(seq.get("playhead").unwrap_or(&Value::Null)),
    )
}

// ---------- handlers (bridge threads; every editor access is a round trip) ----------

fn project_info(link: &Link, _args: &Value) -> Result<String, String> {
    let project = link.execute("project.inspect", json!({}))?;
    let mut text = format!(
        "project \"{}\" ({})",
        project.get("name").and_then(Value::as_str).unwrap_or(""),
        project.get("path").and_then(Value::as_str).unwrap_or("not saved to a file yet"),
    );
    if project.get("dirty").and_then(Value::as_bool) == Some(true) {
        text.push_str(", unsaved changes");
    }
    match link.sequence() {
        Ok(seq) => {
            text.push('\n');
            text.push_str(&sequence_summary(&seq));
        }
        Err(_) => text.push_str("\nno sequence is open"),
    }
    Ok(text)
}

fn open_project(link: &Link, args: &Value) -> Result<String, String> {
    let path = arg_str(args, "path")?;
    link.execute("file.open", json!({"path": path}))?;
    project_info(link, &json!({})).map(|info| format!("opened {path}\n{info}"))
}

fn list_clips(link: &Link, args: &Value) -> Result<String, String> {
    let seq = link.sequence()?;
    let want = args.get("track").and_then(Value::as_str).filter(|s| !s.trim().is_empty());
    let all = tracks(&seq);
    let chosen: Vec<&TrackView<'_>> = all.iter().filter(|t| want.is_none_or(|w| t.matches(w))).collect();
    if chosen.is_empty() {
        let names: Vec<&str> = all.iter().map(|t| t.label.as_str()).collect();
        return Err(format!("no track `{}` in the active sequence; tracks: {}", want.unwrap_or(""), names.join(", ")));
    }
    let lines: Vec<String> = chosen.iter().flat_map(|t| t.items().iter().map(move |i| clip_line(t, i))).collect();
    if lines.is_empty() {
        return Ok(match want {
            Some(w) => format!("no clips on track {w}"),
            None => "the sequence has no clips".to_string(),
        });
    }
    Ok(format!("{} clips\n{}", lines.len(), lines.join("\n")))
}

fn trim_clip(link: &Link, args: &Value) -> Result<String, String> {
    let id = arg_u64(args, "id")?;
    let start = opt_f64(args, "start")?;
    let end = opt_f64(args, "end")?;
    if start.is_none() && end.is_none() {
        return Err("give `start`, `end` or both (timeline seconds)".to_string());
    }
    let seq = link.sequence()?;
    let (_, item) = find_clip(&seq, id)?;
    let (cur_start, cur_end) = (ticks(item.get("start").unwrap_or(&Value::Null)), ticks(item.get("end").unwrap_or(&Value::Null)));
    if let Some(s) = start {
        let delta = Tick::from_seconds_f64(s) - cur_start;
        link.execute("timeline.trim", json!({"clip": id, "edge": "in", "mode": "regular", "delta": delta.0}))?;
    }
    if let Some(e) = end {
        let delta = Tick::from_seconds_f64(e) - cur_end;
        link.execute("timeline.trim", json!({"clip": id, "edge": "out", "mode": "regular", "delta": delta.0}))?;
    }
    let seq = link.sequence()?;
    let (track, item) = find_clip(&seq, id)?;
    Ok(format!("trimmed {}", clip_line(&track, item)))
}

fn split_clip(link: &Link, args: &Value) -> Result<String, String> {
    let id = arg_u64(args, "id")?;
    let at = arg_f64(args, "at")?;
    let seq = link.sequence()?;
    let (track, item) = find_clip(&seq, id)?;
    let (start, end) = (ticks(item.get("start").unwrap_or(&Value::Null)), ticks(item.get("end").unwrap_or(&Value::Null)));
    let cut = Tick::from_seconds_f64(at);
    if cut <= start || cut >= end {
        return Err(format!("{at} s is not inside clip #{id} ({} s - {} s)", secs(&json!(start.0)), secs(&json!(end.0))));
    }
    let track_id = track.id();
    let result = link.execute("timeline.razor", json!({"clip": id, "seconds": at}))?;
    let cuts = result.get("cuts").and_then(Value::as_u64).unwrap_or(0);
    if cuts == 0 {
        return Err(format!("nothing was cut at {at} s (the clip's track may be locked)"));
    }
    // The pieces: the clips on that track that now meet at the cut.
    let seq = link.sequence()?;
    let pieces: Vec<String> = tracks(&seq)
        .into_iter()
        .filter(|t| t.id() == track_id)
        .flat_map(|t| {
            t.items()
                .iter()
                .filter(|i| ticks(i.get("end").unwrap_or(&Value::Null)) == cut || ticks(i.get("start").unwrap_or(&Value::Null)) == cut)
                .map(|i| clip_line(&t, i))
                .collect::<Vec<_>>()
        })
        .collect();
    Ok(format!("split clip #{id} at {at} s ({cuts} cut{})\n{}", if cuts == 1 { "" } else { "s" }, pieces.join("\n")))
}

fn set_playhead(link: &Link, args: &Value) -> Result<String, String> {
    let at = arg_f64(args, "at")?;
    let result = link.execute("playhead.set", json!({"seconds": at}))?;
    Ok(format!("playhead at {} s", secs(result.get("time").unwrap_or(&Value::Null))))
}

fn render(link: &Link, args: &Value) -> Result<String, String> {
    let path = match args.get("path").and_then(Value::as_str).map(str::trim).filter(|s| !s.is_empty()) {
        Some(p) => p.to_string(),
        None => {
            // The project's folder, as the Export dialog defaults to; home when it has no file.
            let project = link.execute("project.inspect", json!({}))?;
            project
                .get("path")
                .and_then(Value::as_str)
                .and_then(|p| std::path::Path::new(p).parent())
                .filter(|d| !d.as_os_str().is_empty())
                .map(|d| format!("{}{}", d.display(), std::path::MAIN_SEPARATOR))
                .unwrap_or_else(|| DEFAULT_RENDER_DIR.to_string())
        }
    };
    let mut params = json!({"path": path});
    if let Some(preset) = args.get("preset").and_then(Value::as_str).map(str::trim).filter(|s| !s.is_empty()) {
        params["preset"] = json!(preset);
    }
    let result = link.execute("file.exportMedia", params)?;
    let job = result.get("job").and_then(Value::as_u64).ok_or("the export started but reported no job id")?;
    let out = result.get("path").and_then(Value::as_str).unwrap_or("");
    let preset = result.get("preset").and_then(Value::as_str).map(|p| format!(" with preset \"{p}\"")).unwrap_or_default();
    Ok(format!("started render job {job}{preset} -> {out}; render_status {{\"job_id\": {job}}} reports its progress"))
}

fn render_status(link: &Link, args: &Value) -> Result<String, String> {
    let want = opt_u64(args, "job_id")?;
    let jobs = link.execute("jobs.list", json!({}))?;
    let jobs = jobs.as_array().cloned().unwrap_or_default();
    let job = match want {
        Some(id) => jobs.iter().find(|j| j.get("id").and_then(Value::as_u64) == Some(id)).ok_or_else(|| format!("no job {id}"))?,
        None => jobs.iter().max_by_key(|j| j.get("id").and_then(Value::as_u64).unwrap_or(0)).ok_or("no render job has been started")?,
    };
    Ok(job_line(job))
}

fn job_line(job: &Value) -> String {
    let id = job.get("id").unwrap_or(&Value::Null);
    let label = job.get("label").and_then(Value::as_str).unwrap_or("job");
    let result = job.get("result").unwrap_or(&Value::Null);
    if job.get("finished").and_then(Value::as_bool) == Some(true) {
        if let Some(e) = result.get("error").and_then(Value::as_str) {
            return format!("job {id} \"{label}\": failed: {e}");
        }
        return match result.get("path").and_then(Value::as_str) {
            Some(path) => {
                let frames = result.get("frames").and_then(Value::as_u64).unwrap_or(0);
                let bytes = result.get("bytes").and_then(Value::as_u64).unwrap_or(0);
                format!("job {id} \"{label}\": finished -> {path} ({frames} frames, {} MB)", bytes / 1_000_000)
            }
            None => format!("job {id} \"{label}\": finished"),
        };
    }
    let percent = (job.get("progress").and_then(Value::as_f64).unwrap_or(0.0) * 100.0).clamp(0.0, 100.0);
    let mut line = format!("job {id} \"{label}\": {percent:.0}% done");
    if let Some(eta) = job.get("etaSeconds").and_then(Value::as_f64) {
        line.push_str(&format!(", about {eta:.0} s left"));
    }
    if let Some(status) = job.get("status").and_then(Value::as_str).filter(|s| !s.is_empty()) {
        line.push_str(&format!(" ({status})"));
    }
    line
}

#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::expect_used, clippy::panic)]
mod tests {
    use super::*;

    fn sample_sequence() -> Value {
        let t = Tick::from_seconds_f64;
        json!({
            "id": 7, "name": "Trailer", "duration": t(10.0).0, "playhead": t(2.5).0,
            "settings": {"width": 1920, "height": 1080, "frame_rate": {"num": 24000, "den": 1001}},
            "video": [
                {"id": 1, "name": "Video 1", "items": [
                    {"clip": 11, "name": "a.mov", "start": 0, "end": t(4.0).0, "sourceIn": 0, "sourceOut": t(4.0).0, "enabled": true},
                    {"clip": 12, "name": "b.mov", "start": t(4.0).0, "end": t(10.0).0, "sourceIn": t(1.0).0, "sourceOut": t(7.0).0, "enabled": false},
                ]},
            ],
            "audio": [{"id": 2, "name": "Audio 1", "items": []}],
        })
    }

    #[test]
    fn tracks_are_labelled_by_kind_and_position() {
        let seq = sample_sequence();
        let all = tracks(&seq);
        assert_eq!(all.iter().map(|t| t.label.as_str()).collect::<Vec<_>>(), ["V1", "A1"]);
        assert!(all[0].matches("v1") && all[0].matches("Video 1") && all[0].matches("1"));
        assert!(!all[0].matches("A1"));
    }

    #[test]
    fn clip_lines_read_in_seconds_and_find_clip_knows_the_ids() {
        let seq = sample_sequence();
        let (track, item) = find_clip(&seq, 12).unwrap();
        assert_eq!(clip_line(&track, item), "#12 V1 \"b.mov\" 4.000s-10.000s source 1.000s-7.000s (disabled)");
        assert!(find_clip(&seq, 99).unwrap_err().contains("no clip #99"));
    }

    #[test]
    fn the_summary_names_rate_size_and_counts() {
        let s = sequence_summary(&sample_sequence());
        assert!(s.contains("duration 10.000 s"), "{s}");
        assert!(s.contains("23.976 fps"), "{s}");
        assert!(s.contains("1920x1080, 1 video / 1 audio tracks, 2 clips"), "{s}");
    }

    #[test]
    fn job_lines_cover_running_finished_and_failed() {
        assert_eq!(
            job_line(&json!({"id": 3, "label": "Export x.mp4", "progress": 0.5, "etaSeconds": 12.4, "finished": false})),
            "job 3 \"Export x.mp4\": 50% done, about 12 s left"
        );
        let done = job_line(&json!({"id": 3, "label": "Export x.mp4", "finished": true, "result": {"path": "/out/x.mp4", "frames": 240, "bytes": 5_000_000}}));
        assert_eq!(done, "job 3 \"Export x.mp4\": finished -> /out/x.mp4 (240 frames, 5 MB)");
        assert!(job_line(&json!({"id": 3, "label": "Export", "finished": true, "result": {"error": "disk full"}})).ends_with("failed: disk full"));
    }

    #[test]
    fn ids_accept_integers_floats_and_hash_strings() {
        assert_eq!(opt_u64(&json!({"id": 5}), "id").unwrap(), Some(5));
        assert_eq!(opt_u64(&json!({"id": 5.0}), "id").unwrap(), Some(5));
        assert_eq!(opt_u64(&json!({"id": "#5"}), "id").unwrap(), Some(5));
        assert!(opt_u64(&json!({"id": -1}), "id").is_err());
        assert_eq!(opt_u64(&json!({}), "id").unwrap(), None);
    }
}
