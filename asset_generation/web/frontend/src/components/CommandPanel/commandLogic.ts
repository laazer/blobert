import { RunCmd } from "../../types";

export const ALL_CMDS: RunCmd[] = ["animated", "player", "level", "smart", "stats", "test"];
export const PLAYER_COLORS = ["blue", "green", "pink", "purple", "yellow", "orange", "red", "white"];
export const PLAYER_FINISHES = ["glossy", "matte", "metallic", "gel"];
export const ENEMY_FINISHES = ["default", "glossy", "matte", "metallic", "gel"];

export type CommandConfig = {
  showEnemy: boolean;
  showDescription: boolean;
  showDifficulty: boolean;
  requiresEnemy: boolean;
};

export const CMD_CONFIG: Record<RunCmd, CommandConfig> = {
  animated: { showEnemy: true, showDescription: false, showDifficulty: false, requiresEnemy: true },
  player: { showEnemy: true, showDescription: false, showDifficulty: false, requiresEnemy: true },
  level: { showEnemy: true, showDescription: false, showDifficulty: false, requiresEnemy: true },
  smart: { showEnemy: false, showDescription: true, showDifficulty: true, requiresEnemy: false },
  stats: { showEnemy: true, showDescription: false, showDifficulty: true, requiresEnemy: true },
  test: { showEnemy: false, showDescription: false, showDifficulty: false, requiresEnemy: false },
};

export function getEnemyOptions(cmd: RunCmd, enemies: string[]): string[] {
  return cmd === "player" ? PLAYER_COLORS : enemies;
}

export function normalizeEnemyForCmd(cmd: RunCmd, enemy: string, enemies: string[]): string {
  const options = getEnemyOptions(cmd, enemies);
  if (!CMD_CONFIG[cmd].showEnemy) return "";
  if (options.length === 0) return enemy;
  if (enemy && options.includes(enemy)) return enemy;
  return options[0];
}

function tokenizeCommand(value: string): string[] {
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g;
  const out: string[] = [];
  let match: RegExpExecArray | null = re.exec(value);
  while (match) {
    out.push(match[1] ?? match[2] ?? match[3]);
    match = re.exec(value);
  }
  return out;
}

export function formatCommandPreview(options: {
  cmd: RunCmd;
  enemy: string;
  description: string;
  difficulty: string;
  finish: string;
  hexColor: string;
}): string {
  const cfg = CMD_CONFIG[options.cmd];
  const parts: string[] = [options.cmd];
  if (cfg.showEnemy && options.enemy.trim()) parts.push(options.enemy.trim());
  if (cfg.showDescription && options.description.trim()) {
    const clean = options.description.trim().replace(/"/g, '\\"');
    parts.push(`--description "${clean}"`);
  }
  if (cfg.showDifficulty && options.difficulty.trim()) parts.push(`--difficulty ${options.difficulty.trim()}`);
  if ((options.cmd === "player" || options.cmd === "animated") && options.finish.trim()) {
    parts.push(`--finish ${options.finish.trim()}`);
  }
  if ((options.cmd === "player" || options.cmd === "animated") && options.hexColor.trim()) {
    parts.push(`--hex-color ${options.hexColor.trim()}`);
  }
  return parts.join(" ");
}

export function parseCommandPreview(preview: string): {
  next: {
    cmd: RunCmd;
    enemy?: string;
    description?: string;
    difficulty?: string;
    finish?: string;
    hexColor?: string;
  } | null;
  error: string | null;
} {
  const tokens = tokenizeCommand(preview.trim());
  if (tokens.length === 0) return { next: null, error: "Command preview is empty." };
  const rawCmd = tokens[0];
  if (!ALL_CMDS.includes(rawCmd as RunCmd)) {
    return { next: null, error: `Unknown cmd '${rawCmd}'.` };
  }
  const cmd = rawCmd as RunCmd;
  const cfg = CMD_CONFIG[cmd];
  let cursor = 1;
  const next: {
    cmd: RunCmd;
    enemy?: string;
    description?: string;
    difficulty?: string;
    finish?: string;
    hexColor?: string;
  } = { cmd };
  const positional: string[] = [];
  while (cursor < tokens.length && !tokens[cursor].startsWith("--")) {
    positional.push(tokens[cursor]);
    cursor += 1;
  }
  if (cfg.showEnemy && positional.length > 0) next.enemy = positional[0];
  if (cfg.showEnemy && positional.length > 1) return { next: null, error: "Too many positional values." };
  if (!cfg.showEnemy && positional.length > 0) return { next: null, error: `'${cmd}' does not take positional enemy/count values.` };
  while (cursor < tokens.length) {
    const flag = tokens[cursor];
    const value = tokens[cursor + 1];
    if (!value || value.startsWith("--")) {
      return { next: null, error: `Missing value for ${flag}.` };
    }
    if (flag === "--description") {
      if (!cfg.showDescription) return { next: null, error: `'${cmd}' does not use --description.` };
      next.description = value;
    } else if (flag === "--difficulty") {
      if (!cfg.showDifficulty) return { next: null, error: `'${cmd}' does not use --difficulty.` };
      next.difficulty = value;
    } else if (flag === "--finish") {
      if (cmd !== "player" && cmd !== "animated") return { next: null, error: `'${cmd}' does not use --finish.` };
      const validFinishes = cmd === "player" ? PLAYER_FINISHES : ENEMY_FINISHES;
      if (!validFinishes.includes(value)) {
        return { next: null, error: `Unknown finish '${value}'.` };
      }
      next.finish = value;
    } else if (flag === "--hex-color") {
      if (cmd !== "player" && cmd !== "animated") return { next: null, error: `'${cmd}' does not use --hex-color.` };
      if (!/^#[0-9a-fA-F]{6}$/.test(value)) {
        return { next: null, error: "hex color must be #RRGGBB." };
      }
      next.hexColor = value;
    } else {
      return { next: null, error: `Unknown flag '${flag}'.` };
    }
    cursor += 2;
  }
  if (cfg.requiresEnemy && !next.enemy?.trim()) {
    return { next: null, error: `'${cmd}' requires an enemy.` };
  }
  return { next, error: null };
}
