import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const gulpfilePath = path.resolve(testDir, "..", "gulpfile.js");

test("local BrowserSync does not mirror operator actions between windows", async () => {
  const gulpfile = await readFile(gulpfilePath, "utf8");

  assert.match(gulpfile, /ghostMode:\s*false/);
});
