// Keep Gentle Agents' session transport isolated to this project.
//
// gentle-pi scopes orchestrator discovery to GENTLE_PI_AGENT_HOME. Its default
// (~/.pi/agent) is shared by every Pi process on the machine, so unrelated
// repositories can discover each other and exchange triggerTurn notifications.
//
// Project extensions load before package extensions in Pi. Set the Gentle-only
// agent home here, before gentle-pi initializes. PI_CODING_AGENT_DIR is left
// untouched, so Pi auth/settings/packages remain global as normal.
//
// Set PI_NAN_ALLOW_SHARED_GENTLE_HOME=1 only when cross-project orchestrator
// discovery is explicitly desired.

import { copyFileSync, cpSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const PROJECT_AGENT_HOME = join(PROJECT_ROOT, ".pi", "gentle-agent-home");
const ALLOW_SHARED_ENV = "PI_NAN_ALLOW_SHARED_GENTLE_HOME";

function resolveAgentHome(value) {
	if (!value) return join(homedir(), ".pi", "agent");
	if (value === "~") return homedir();
	if (value.startsWith("~/") || value.startsWith("~\\")) return join(homedir(), value.slice(2));
	return resolve(value);
}

function seedDirectory(source, target) {
	if (!existsSync(source)) return;
	mkdirSync(target, { recursive: true });
	cpSync(source, target, { recursive: true, force: false, errorOnExist: false });
}

export default function () {
	if (process.env[ALLOW_SHARED_ENV] === "1") return;

	const sourceHome = resolveAgentHome(
		process.env.GENTLE_PI_AGENT_HOME || process.env.PI_CODING_AGENT_DIR,
	);

	mkdirSync(PROJECT_AGENT_HOME, { recursive: true });

	// Preserve existing global/custom agent definitions on first use without
	// sharing runtime/session state between projects. Existing project-local
	// files win; later starts only fill files that are still missing.
	if (resolve(sourceHome) !== resolve(PROJECT_AGENT_HOME)) {
		seedDirectory(join(sourceHome, "agents"), join(PROJECT_AGENT_HOME, "agents"));
		seedDirectory(join(sourceHome, "subagents"), join(PROJECT_AGENT_HOME, "subagents"));

		const sourceConfig = join(sourceHome, "subagents.json");
		const targetConfig = join(PROJECT_AGENT_HOME, "subagents.json");
		if (existsSync(sourceConfig) && !existsSync(targetConfig)) {
			copyFileSync(sourceConfig, targetConfig);
		}
	}

	process.env.GENTLE_PI_AGENT_HOME = PROJECT_AGENT_HOME;
}
