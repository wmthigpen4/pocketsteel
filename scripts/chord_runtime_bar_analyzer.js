#!/usr/bin/env node
"use strict";

// Content-bound target-browser harness for the exact Play Along decode, mono,
// downsample, and rhythm-analysis path. Audio bytes are embedded into an
// about:blank document; all page network requests are blocked and audited.

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

const OUTPUT_SCHEMA = "chord_runtime_browser_bar_analyzer_output_v1";
const SOURCE_ID = "play-along-target-chrome-webaudio-rhythm-analysis-v1";
const BROWSER_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const CLIENT_PATH = path.resolve(__dirname, "../ui/practice-analysis-client.js");
const WORKER_PATH = path.resolve(__dirname, "../ui/practice-analysis-worker.js");
const ANALYSIS_TIMEOUT_MS = 240000;
const BROWSER_LAUNCH_TIMEOUT_MS = 30000;
const BROWSER_FLAGS = [
  "--headless=new",
  "--remote-debugging-port=0",
  "--no-first-run",
  "--disable-background-networking",
  "--disable-component-update",
  "--disable-default-apps",
  "--disable-domain-reliability",
  "--disable-extensions",
  "--disable-features=OptimizationHints,MediaRouter",
  "--disable-sync",
  "--metrics-recording-only",
  "--mute-audio",
  "--host-resolver-rules=MAP * ~NOTFOUND",
  "--no-proxy-server",
  "--proxy-server=direct://",
  "--proxy-bypass-list=*",
];
const AUDIO_MIME = {
  ".aac": "audio/aac",
  ".m4a": "audio/mp4",
  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
};

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith("--")) throw new Error(`Unexpected argument ${key}.`);
    const value = argv[index + 1];
    if (value === undefined || value.startsWith("--")) throw new Error(`${key} needs a value.`);
    values[key.slice(2)] = value;
    index += 1;
  }
  const allowed = new Set([
    "audio",
    "expected-audio-sha256",
    "expected-browser-sha256",
    "expected-browser-version",
    "expected-client-sha256",
    "expected-node-sha256",
    "expected-node-version",
    "expected-runner-sha256",
    "expected-worker-sha256",
  ]);
  const unexpected = Object.keys(values).filter((key) => !allowed.has(key));
  if (unexpected.length) throw new Error(`Unsupported argument --${unexpected.sort()[0]}.`);
  for (const required of allowed) {
    if (!values[required]) throw new Error(`--${required} is required.`);
  }
  return values;
}

function sha256Bytes(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function sha256File(filePath) {
  return sha256Bytes(fs.readFileSync(filePath));
}

function requireExpectedSha256(value, label) {
  if (!/^[0-9a-f]{64}$/.test(value)) throw new Error(`${label} must be a lowercase SHA-256 digest.`);
}

function verifySources(values) {
  const identities = {
    browserExecutableSha256: sha256File(BROWSER_PATH),
    clientSha256: sha256File(CLIENT_PATH),
    nodeExecutableSha256: sha256File(process.execPath),
    runnerSha256: sha256File(__filename),
    workerSha256: sha256File(WORKER_PATH),
  };
  const expectations = {
    browserExecutableSha256: values["expected-browser-sha256"],
    clientSha256: values["expected-client-sha256"],
    nodeExecutableSha256: values["expected-node-sha256"],
    runnerSha256: values["expected-runner-sha256"],
    workerSha256: values["expected-worker-sha256"],
  };
  Object.entries(expectations).forEach(([name, expected]) => {
    requireExpectedSha256(expected, name);
    if (identities[name] !== expected) throw new Error(`${name} does not match the bound source contract.`);
  });
  if (process.version !== values["expected-node-version"]) {
    throw new Error("The Node runtime version does not match the bound source contract.");
  }
  return identities;
}

function canonicalSha256(value) {
  return sha256Bytes(Buffer.from(JSON.stringify(value), "utf8"));
}

function escapeInlineScript(source) {
  return source.replaceAll("</script", "<\\/script");
}

function browserDocument(audioBytes, suffix) {
  const clientSource = escapeInlineScript(fs.readFileSync(CLIENT_PATH, "utf8"));
  const workerSource = escapeInlineScript(fs.readFileSync(WORKER_PATH, "utf8"));
  const audioBase64 = audioBytes.toString("base64");
  const mime = AUDIO_MIME[suffix];
  return `<!doctype html>
<html><head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; connect-src 'none'; media-src 'none'; img-src 'none'; worker-src 'none';">
</head><body data-runtime-status="running"><pre id="result"></pre>
<script>${clientSource}</script>
<script>${workerSource}</script>
<script>
(async () => {
  const resultNode = document.getElementById("result");
  const digest = (view) => {
    const input = new Uint8Array(view.buffer, view.byteOffset, view.byteLength);
    const paddedLength = Math.ceil((input.length + 9) / 64) * 64;
    const padded = new Uint8Array(paddedLength);
    padded.set(input);
    padded[input.length] = 0x80;
    const bitLength = input.length * 8;
    const data = new DataView(padded.buffer);
    data.setUint32(paddedLength - 8, Math.floor(bitLength / 0x100000000), false);
    data.setUint32(paddedLength - 4, bitLength >>> 0, false);
    const constants = [
      0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
      0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
      0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
      0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
      0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
      0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
      0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,
    ];
    const state = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const words = new Uint32Array(64);
    const rotate = (value, bits) => (value >>> bits) | (value << (32 - bits));
    for (let offset = 0; offset < paddedLength; offset += 64) {
      for (let index = 0; index < 16; index += 1) words[index] = data.getUint32(offset + index * 4, false);
      for (let index = 16; index < 64; index += 1) {
        const left = words[index - 15], right = words[index - 2];
        const sigma0 = rotate(left, 7) ^ rotate(left, 18) ^ (left >>> 3);
        const sigma1 = rotate(right, 17) ^ rotate(right, 19) ^ (right >>> 10);
        words[index] = (words[index - 16] + sigma0 + words[index - 7] + sigma1) >>> 0;
      }
      let [a,b,c,d,e,f,g,h] = state;
      for (let index = 0; index < 64; index += 1) {
        const upper1 = rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25);
        const choice = (e & f) ^ (~e & g);
        const temporary1 = (h + upper1 + choice + constants[index] + words[index]) >>> 0;
        const upper0 = rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22);
        const majority = (a & b) ^ (a & c) ^ (b & c);
        const temporary2 = (upper0 + majority) >>> 0;
        h=g;g=f;f=e;e=(d+temporary1)>>>0;d=c;c=b;b=a;a=(temporary1+temporary2)>>>0;
      }
      [a,b,c,d,e,f,g,h].forEach((value, index) => { state[index] = (state[index] + value) >>> 0; });
    }
    return state.map((value) => value.toString(16).padStart(8, "0")).join("");
  };
  try {
    const binary = atob("${audioBase64}");
    const audioBytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) audioBytes[index] = binary.charCodeAt(index);
    const file = new File([audioBytes], "allowed-input${suffix}", { type: "${mime}" });
    const decoded = await STEEL_RAG_ANALYSIS_CLIENT.decodeAudio(file);
    const mono = STEEL_RAG_ANALYSIS_CLIENT.monoSamples(decoded);
    const canonicalDurationMs = Math.round(Number(decoded.duration) * 1000);
    const reduced = STEEL_RAG_ANALYSIS_V2.downsample(mono, decoded.sampleRate);
    const rhythm = STEEL_RAG_ANALYSIS_V2.rhythmAnalysis(
      reduced.samples,
      reduced.sampleRate,
      canonicalDurationMs,
      {},
    );
    const littleEndian = new Uint8Array(new Uint32Array([0x01020304]).buffer)[0] === 4;
    const output = {
      sourceAudioSha256: digest(audioBytes),
      decodedPcmSha256: digest(mono),
      decodedPcmSampleCount: mono.length,
      decodedSampleRateHz: decoded.sampleRate,
      decodedChannelCount: decoded.numberOfChannels,
      decodedDurationSeconds: Number(decoded.duration),
      canonicalDurationMilliseconds: canonicalDurationMs,
      analyzerPcmSha256: digest(reduced.samples),
      analyzerPcmSampleCount: reduced.samples.length,
      analyzerSampleRateHz: reduced.sampleRate,
      float32ByteOrder: littleEndian ? "little-endian" : "big-endian",
      secureContext: isSecureContext,
      navigatorUserAgent: navigator.userAgent,
      navigatorPlatform: navigator.platform,
      analysisVersion: Number(STEEL_RAG_ANALYSIS_V2.ANALYSIS_VERSION),
      beatTimesSeconds: (rhythm.beatTimesMs || []).map((value) => Number(value) / 1000),
      barStartsSeconds: (rhythm.barStartsMs || []).map((value) => Number(value) / 1000),
      meter: String(rhythm.meter || ""),
      beatsPerBar: Number(rhythm.beatsPerBar),
      tempo: Number(rhythm.tempo),
    };
    resultNode.textContent = JSON.stringify(output);
    document.body.dataset.runtimeStatus = "complete";
  } catch (error) {
    resultNode.textContent = error instanceof Error ? error.message : String(error);
    document.body.dataset.runtimeStatus = "error";
  }
})();
</script></body></html>`;
}

class CdpConnection {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.onEvent = () => {};
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(message.error.message));
        else pending.resolve(message.result || {});
      } else this.onEvent(message);
    });
  }

  send(method, params = {}, sessionId = undefined) {
    const id = this.nextId++;
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Chrome DevTools command ${method} timed out.`));
      }, 30000);
      this.pending.set(id, {
        resolve: (value) => { clearTimeout(timer); resolve(value); },
        reject: (error) => { clearTimeout(timer); reject(error); },
      });
      this.socket.send(JSON.stringify(payload));
    });
  }
}

function connectWebSocket(url) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(url);
    const timer = setTimeout(() => reject(new Error("Chrome DevTools connection timed out.")), 15000);
    socket.addEventListener("open", () => { clearTimeout(timer); resolve(socket); }, { once: true });
    socket.addEventListener("error", () => { clearTimeout(timer); reject(new Error("Chrome DevTools connection failed.")); }, { once: true });
  });
}

function launchBrowser(userDataDir) {
  return new Promise((resolve, reject) => {
    const child = spawn(
      BROWSER_PATH,
      [...BROWSER_FLAGS, `--user-data-dir=${userDataDir}`, "about:blank"],
      { stdio: ["ignore", "ignore", "pipe"] },
    );
    let stderr = "";
    let settled = false;
    const launchError = (reason) => {
      const detail = stderr.trim().slice(-2048);
      return new Error(`${reason}${detail ? ` Chrome stderr tail: ${detail}` : ""}`);
    };
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      const error = launchError("Target Chrome did not publish a DevTools endpoint.");
      void terminateBrowser(child).then(
        () => reject(error),
        () => reject(error),
      );
    }, BROWSER_LAUNCH_TIMEOUT_MS);
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk) => {
      stderr = `${stderr}${chunk}`.slice(-8192);
      const match = /DevTools listening on (ws:\/\/[^\s]+)/.exec(stderr);
      if (!match || settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ child, webSocketUrl: match[1] });
    });
    child.once("error", (error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(launchError(`Target Chrome could not start: ${error.message}.`));
    });
    child.once("exit", (code, signal) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(
        launchError(
          `Target Chrome exited before analysis (code=${String(code)}, signal=${String(signal)}).`,
        ),
      );
    });
  });
}

async function waitForBrowserResult(cdp, sessionId) {
  const deadline = Date.now() + ANALYSIS_TIMEOUT_MS;
  while (Date.now() < deadline) {
    const evaluation = await cdp.send(
      "Runtime.evaluate",
      {
        expression: `({status: document.body?.dataset?.runtimeStatus || "", result: document.getElementById("result")?.textContent || ""})`,
        returnByValue: true,
      },
      sessionId,
    );
    const value = evaluation.result?.value || {};
    if (value.status === "complete") return JSON.parse(value.result);
    if (value.status === "error") throw new Error(`Target-browser analysis failed: ${value.result}`);
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("Target-browser audio analysis timed out.");
}

async function terminateBrowser(child) {
  if (!child || child.exitCode !== null) return;
  child.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => child.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, 5000)),
  ]);
  if (child.exitCode !== null) return;
  child.kill("SIGKILL");
  await Promise.race([
    new Promise((resolve) => child.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, 5000)),
  ]);
}

async function analyzeInBrowser(audioBytes, suffix, expectedBrowserVersion) {
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "chord-runtime-browser-"));
  let browser;
  let socket;
  try {
    browser = await launchBrowser(userDataDir);
    socket = await connectWebSocket(browser.webSocketUrl);
    const cdp = new CdpConnection(socket);
    const browserVersion = await cdp.send("Browser.getVersion");
    if (!String(browserVersion.product || "").endsWith(`/${expectedBrowserVersion}`)) {
      throw new Error("The running browser version does not match the bound source contract.");
    }
    const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
    const { sessionId } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
    const networkRequests = [];
    cdp.onEvent = (message) => {
      if (message.sessionId === sessionId && message.method === "Network.requestWillBeSent") {
        networkRequests.push(String(message.params?.request?.url || ""));
      }
    };
    await cdp.send("Page.enable", {}, sessionId);
    await cdp.send("Runtime.enable", {}, sessionId);
    await cdp.send("Network.enable", {}, sessionId);
    await cdp.send("Network.setCacheDisabled", { cacheDisabled: true }, sessionId);
    await cdp.send("Network.setBlockedURLs", { urls: ["http://*", "https://*", "file://*", "ftp://*"] }, sessionId);
    const frameTree = await cdp.send("Page.getFrameTree", {}, sessionId);
    await cdp.send(
      "Page.setDocumentContent",
      { frameId: frameTree.frameTree.frame.id, html: browserDocument(audioBytes, suffix) },
      sessionId,
    );
    const analysis = await waitForBrowserResult(cdp, sessionId);
    if (networkRequests.length) {
      throw new Error(`Browser harness attempted ${networkRequests.length} secondary network request(s).`);
    }
    return {
      analysis,
      browserVersion,
      browserLaunchContractSha256: canonicalSha256(BROWSER_FLAGS),
      networkRequestCount: networkRequests.length,
    };
  } finally {
    if (socket) socket.close();
    await terminateBrowser(browser?.child);
    try { fs.rmSync(userDataDir, { recursive: true, force: true }); } catch (_error) {}
  }
}

async function main() {
  const values = parseArgs(process.argv.slice(2));
  const identities = verifySources(values);
  const audioPath = path.resolve(values.audio);
  const suffix = path.extname(audioPath).toLowerCase();
  if (!Object.hasOwn(AUDIO_MIME, suffix)) throw new Error("The audio suffix is not in the self-contained browser allowlist.");
  if (!fs.statSync(audioPath).isFile()) throw new Error("--audio must point to a regular file.");
  const audioBytes = fs.readFileSync(audioPath);
  const sourceAudioSha256 = sha256Bytes(audioBytes);
  requireExpectedSha256(values["expected-audio-sha256"], "--expected-audio-sha256");
  if (sourceAudioSha256 !== values["expected-audio-sha256"]) {
    throw new Error("The audio bytes do not match the caller's exact allowlist binding.");
  }
  const browserVersion = String(values["expected-browser-version"]);
  const browser = await analyzeInBrowser(audioBytes, suffix, browserVersion);
  if (browser.analysis.sourceAudioSha256 !== sourceAudioSha256) {
    throw new Error("The browser did not decode the exact allowlisted audio bytes.");
  }
  const output = {
    schemaVersion: OUTPUT_SCHEMA,
    sourceId: SOURCE_ID,
    ...identities,
    nodeVersion: process.version,
    browserProduct: String(browser.browserVersion.product || ""),
    browserRevision: String(browser.browserVersion.revision || ""),
    browserProtocolVersion: String(browser.browserVersion.protocolVersion || ""),
    browserJavaScriptVersion: String(browser.browserVersion.jsVersion || ""),
    browserLaunchContractSha256: browser.browserLaunchContractSha256,
    networkRequestCount: browser.networkRequestCount,
    ...browser.analysis,
  };
  process.stdout.write(`${JSON.stringify(output)}\n`);
}

main().catch((error) => {
  process.stderr.write(`${error instanceof Error ? error.message : error}\n`);
  process.exitCode = 1;
});
