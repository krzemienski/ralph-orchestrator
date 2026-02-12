//! Cloudflare tunnel management commands.
//!
//! Provides:
//! - `ralph tunnel start` — Start a named Cloudflare tunnel to expose ralph-mobile-server
//! - `ralph tunnel status` — Check if a tunnel is currently running
//! - `ralph tunnel stop` — Stop the running tunnel and clean up state

use anyhow::{anyhow, Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::{Command, Stdio};

// ─────────────────────────────────────────────────────────────────────────────
// CLI STRUCTS
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Parser, Debug)]
pub struct TunnelArgs {
    #[command(subcommand)]
    pub command: TunnelCommands,
}

#[derive(Subcommand, Debug)]
pub enum TunnelCommands {
    /// Start a Cloudflare tunnel to expose ralph-mobile-server
    Start(StartArgs),
    /// Check tunnel status
    Status,
    /// Stop the running tunnel
    Stop,
}

#[derive(Parser, Debug)]
pub struct StartArgs {
    /// Server port to tunnel (default: 8080)
    #[arg(long, default_value = "8080")]
    pub port: u16,

    /// Custom domain (requires Cloudflare DNS configuration)
    #[arg(long)]
    pub domain: Option<String>,

    /// Tunnel name (default: "ralph-mobile")
    #[arg(long, default_value = "ralph-mobile")]
    pub name: String,
}

// ─────────────────────────────────────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
pub struct TunnelState {
    pub url: String,
    pub name: String,
    pub port: u16,
    pub pid: u32,
    pub started_at: String,
}

fn state_file_path() -> PathBuf {
    PathBuf::from(".ralph/tunnel.json")
}

fn read_state() -> Option<TunnelState> {
    let path = state_file_path();
    if !path.exists() {
        return None;
    }
    let contents = std::fs::read_to_string(&path).ok()?;
    serde_json::from_str(&contents).ok()
}

fn write_state(state: &TunnelState) -> Result<()> {
    let path = state_file_path();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let json = serde_json::to_string_pretty(state)?;
    std::fs::write(&path, json)?;
    Ok(())
}

fn remove_state() {
    let path = state_file_path();
    let _ = std::fs::remove_file(path);
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────

fn print_success(use_colors: bool, msg: &str) {
    if use_colors {
        println!("\x1b[32m✓\x1b[0m {msg}");
    } else {
        println!("OK: {msg}");
    }
}

fn _print_error(use_colors: bool, msg: &str) {
    if use_colors {
        eprintln!("\x1b[31m✗\x1b[0m {msg}");
    } else {
        eprintln!("ERROR: {msg}");
    }
}

fn print_info(use_colors: bool, msg: &str) {
    if use_colors {
        println!("\x1b[36mℹ\x1b[0m {msg}");
    } else {
        println!("INFO: {msg}");
    }
}

fn print_warning(use_colors: bool, msg: &str) {
    if use_colors {
        println!("\x1b[33m⚠\x1b[0m {msg}");
    } else {
        println!("WARN: {msg}");
    }
}

fn check_cloudflared() -> Result<PathBuf> {
    let output = Command::new("which")
        .arg("cloudflared")
        .output()
        .context("Failed to search for cloudflared")?;

    if !output.status.success() {
        return Err(anyhow!(
            "cloudflared not found.\n\n\
             Install it with one of:\n  \
             brew install cloudflared          # macOS\n  \
             sudo apt install cloudflared      # Debian/Ubuntu\n  \
             curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared  # Linux binary\n\n\
             Then authenticate: cloudflared tunnel login"
        ));
    }

    let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
    Ok(PathBuf::from(path))
}

fn check_server_health(port: u16) -> bool {
    let url = format!("http://127.0.0.1:{port}/health");
    // Use a simple TCP check + HTTP GET via std::process curl
    let result = Command::new("curl")
        .args(["-sf", "--max-time", "3", &url])
        .output();

    match result {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}

fn is_process_running(pid: u32) -> bool {
    // Check if process exists via kill -0
    Command::new("kill")
        .args(["-0", &pid.to_string()])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

// ─────────────────────────────────────────────────────────────────────────────
// DISPATCHER
// ─────────────────────────────────────────────────────────────────────────────

pub fn execute(args: TunnelArgs, use_colors: bool) -> Result<()> {
    match args.command {
        TunnelCommands::Start(start_args) => tunnel_start(start_args, use_colors),
        TunnelCommands::Status => tunnel_status(use_colors),
        TunnelCommands::Stop => tunnel_stop(use_colors),
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// COMMANDS
// ─────────────────────────────────────────────────────────────────────────────

fn tunnel_start(args: StartArgs, use_colors: bool) -> Result<()> {
    // 1. Check for existing tunnel
    if let Some(state) = read_state() {
        if is_process_running(state.pid) {
            print_info(
                use_colors,
                &format!("Tunnel already running: {} (PID {})", state.url, state.pid),
            );
            return Ok(());
        }
        // Stale state file — clean up
        print_warning(use_colors, "Found stale tunnel state, cleaning up...");
        remove_state();
    }

    // 2. Check cloudflared is installed
    let cf_path = check_cloudflared()?;
    print_success(
        use_colors,
        &format!("cloudflared found at {}", cf_path.display()),
    );

    // 3. Check mobile-server is running
    if !check_server_health(args.port) {
        print_warning(
            use_colors,
            &format!(
                "ralph-mobile-server not detected on port {}. Start it with:\n  \
                 cargo run --bin ralph-mobile-server -- --bind-all",
                args.port
            ),
        );
    } else {
        print_success(
            use_colors,
            &format!("ralph-mobile-server healthy on port {}", args.port),
        );
    }

    // 4. Ensure named tunnel exists (create if needed)
    print_info(
        use_colors,
        &format!("Ensuring tunnel '{}' exists...", args.name),
    );
    let create_output = Command::new("cloudflared")
        .args(["tunnel", "create", &args.name])
        .output();

    match create_output {
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            if output.status.success() {
                print_success(use_colors, &format!("Created tunnel '{}'", args.name));
            } else if stderr.contains("already exists") {
                print_info(
                    use_colors,
                    &format!("Tunnel '{}' already exists, reusing", args.name),
                );
            } else {
                return Err(anyhow!(
                    "Failed to create tunnel '{}': {}",
                    args.name,
                    stderr.trim()
                ));
            }
        }
        Err(e) => return Err(anyhow!("Failed to run cloudflared: {e}")),
    }

    // 5. Configure tunnel route (if custom domain)
    if let Some(ref domain) = args.domain {
        print_info(
            use_colors,
            &format!("Routing tunnel to {domain}..."),
        );
        let route_output = Command::new("cloudflared")
            .args([
                "tunnel",
                "route",
                "dns",
                &args.name,
                domain,
            ])
            .output()
            .context("Failed to configure tunnel route")?;

        if route_output.status.success() {
            print_success(use_colors, &format!("DNS route configured for {domain}"));
        } else {
            let stderr = String::from_utf8_lossy(&route_output.stderr);
            if !stderr.contains("already exists") {
                print_warning(
                    use_colors,
                    &format!("DNS route warning: {}", stderr.trim()),
                );
            }
        }
    }

    // 6. Start the tunnel
    let tunnel_url = if let Some(ref domain) = args.domain {
        format!("https://{domain}")
    } else {
        format!("https://{}.cfargotunnel.com", args.name)
    };

    print_info(use_colors, "Starting tunnel...");

    let child = Command::new("cloudflared")
        .args([
            "tunnel",
            "--url",
            &format!("http://127.0.0.1:{}", args.port),
            "run",
            &args.name,
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::piped())
        .spawn()
        .context("Failed to start cloudflared tunnel")?;

    let pid = child.id();
    let started_at = chrono::Utc::now().to_rfc3339();

    // 7. Write state file
    let state = TunnelState {
        url: tunnel_url.clone(),
        name: args.name.clone(),
        port: args.port,
        pid,
        started_at,
    };
    write_state(&state)?;

    // 8. Report success
    println!();
    print_success(
        use_colors,
        &format!("Tunnel running at {tunnel_url}"),
    );
    print_info(use_colors, &format!("PID: {pid}"));
    print_info(
        use_colors,
        &format!("State: {}", state_file_path().display()),
    );
    println!();
    print_info(
        use_colors,
        "Enter this URL in Ralph Mobile → Cloudflare Tunnel setup",
    );
    print_info(use_colors, "Stop with: ralph tunnel stop");

    Ok(())
}

fn tunnel_status(use_colors: bool) -> Result<()> {
    match read_state() {
        Some(state) => {
            if is_process_running(state.pid) {
                let started =
                    chrono::DateTime::parse_from_rfc3339(&state.started_at).ok();
                let uptime = started.map(|s| {
                    let duration = chrono::Utc::now().signed_duration_since(s);
                    let hours = duration.num_hours();
                    let minutes = duration.num_minutes() % 60;
                    if hours > 0 {
                        format!("{hours}h {minutes}m")
                    } else {
                        format!("{minutes}m")
                    }
                });

                println!();
                print_success(
                    use_colors,
                    &format!("Tunnel: {}", state.url),
                );
                print_info(use_colors, &format!("Name: {}", state.name));
                print_info(use_colors, &format!("Port: {}", state.port));
                print_info(use_colors, &format!("PID: {}", state.pid));
                if let Some(uptime) = uptime {
                    print_info(use_colors, &format!("Uptime: {uptime}"));
                }
            } else {
                print_warning(
                    use_colors,
                    "Tunnel process not running (stale state). Cleaning up...",
                );
                remove_state();
            }
        }
        None => {
            print_info(use_colors, "No tunnel running");
        }
    }
    Ok(())
}

fn tunnel_stop(use_colors: bool) -> Result<()> {
    match read_state() {
        Some(state) => {
            if is_process_running(state.pid) {
                // Send SIGTERM for graceful shutdown
                let kill_result = Command::new("kill")
                    .arg(state.pid.to_string())
                    .output();

                match kill_result {
                    Ok(output) if output.status.success() => {
                        print_success(
                            use_colors,
                            &format!(
                                "Tunnel '{}' stopped (PID {})",
                                state.name, state.pid
                            ),
                        );
                    }
                    _ => {
                        // Try SIGKILL as fallback
                        let _ = Command::new("kill")
                            .args(["-9", &state.pid.to_string()])
                            .output();
                        print_warning(
                            use_colors,
                            &format!(
                                "Force-killed tunnel '{}' (PID {})",
                                state.name, state.pid
                            ),
                        );
                    }
                }
            } else {
                print_info(
                    use_colors,
                    "Tunnel process was not running (stale state)",
                );
            }
            remove_state();
            print_success(use_colors, "Tunnel state cleaned up");
        }
        None => {
            print_info(use_colors, "No tunnel running");
        }
    }
    Ok(())
}

// ─────────────────────────────────────────────────────────────────────────────
// TESTS
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_state_serialization() {
        let state = TunnelState {
            url: "https://ralph-mobile.cfargotunnel.com".to_string(),
            name: "ralph-mobile".to_string(),
            port: 8080,
            pid: 12345,
            started_at: "2026-02-10T20:00:00Z".to_string(),
        };

        let json = serde_json::to_string(&state).unwrap();
        let deserialized: TunnelState = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.url, state.url);
        assert_eq!(deserialized.name, state.name);
        assert_eq!(deserialized.port, state.port);
        assert_eq!(deserialized.pid, state.pid);
    }

    #[test]
    fn test_state_file_path() {
        let path = state_file_path();
        assert_eq!(path, PathBuf::from(".ralph/tunnel.json"));
    }

    #[test]
    fn test_is_process_not_running() {
        // PID 999999999 almost certainly doesn't exist
        assert!(!is_process_running(999_999_999));
    }
}
