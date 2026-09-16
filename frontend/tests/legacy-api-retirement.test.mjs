import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const testDir = path.dirname(fileURLToPath(import.meta.url));
const sourcePath = path.resolve(testDir, '..', 'src', 'js', 'main.js');

test('active frontend bootstrap contains no retired diamonds API handler', async () => {
  const source = await readFile(sourcePath, 'utf8');

  assert.doesNotMatch(source, /\/diamonds(?:\/|\b)/);
});
