// Entry for the 17 November 2026 one-day news image.
//
// The image itself (entry.png, rendered by tools/render.py from the day's
// researched stories) is the entry; this program's job is to hand it to the
// grader intact. Before copying, it re-checks the gate the rules state so a
// broken render fails loudly here instead of silently scoring 0:
//   - PNG or JPEG, told apart by its first bytes;
//   - at most 1 MiB (1048576 bytes);
//   - at most 1024 by 1024 pixels (read from the PNG IHDR chunk, or from
//     the first JPEG start-of-frame segment).
// The destination is /output, or $MAKEFUN_OUTPUT_DIR outside the grader's
// container (e.g. `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts`).

import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const MAX_BYTES = 1048576;
const MAX_SIDE = 1024;

const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const JPEG_MAGIC = Buffer.from([0xff, 0xd8, 0xff]);

function fail(message) {
  throw new Error(`entry image rejected: ${message}`);
}

function pngDimensions(buf) {
  if (buf.length < 33 || buf.toString('ascii', 12, 16) !== 'IHDR') {
    fail('PNG header has no IHDR chunk where expected');
  }
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

function jpegDimensions(buf) {
  // Walk JPEG markers until a start-of-frame segment (SOF0/SOF1/SOF2)
  // gives the height and width; skip segments we do not need.
  let offset = 2;
  while (offset + 9 < buf.length) {
    if (buf[offset] !== 0xff) fail('JPEG marker stream is malformed');
    const marker = buf[offset + 1];
    const length = buf.readUInt16BE(offset + 2);
    if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
      return { width: buf.readUInt16BE(offset + 7), height: buf.readUInt16BE(offset + 5) };
    }
    offset += 2 + length;
  }
  fail('JPEG has no start-of-frame segment');
}

const source = new URL('./entry.png', import.meta.url);
const image = readFileSync(source);

let format;
let dimensions;
if (image.subarray(0, 8).equals(PNG_MAGIC)) {
  format = 'PNG';
  dimensions = pngDimensions(image);
} else if (image.subarray(0, 3).equals(JPEG_MAGIC)) {
  format = 'JPEG';
  dimensions = jpegDimensions(image);
} else {
  fail('first bytes are neither PNG nor JPEG');
}
if (image.length > MAX_BYTES) {
  fail(`${format} is ${image.length} bytes, over the 1 MiB limit`);
}
if (dimensions.width > MAX_SIDE || dimensions.height > MAX_SIDE) {
  fail(`${format} is ${dimensions.width}x${dimensions.height}, over the 1024x1024 limit`);
}

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
const destination = join(outDir, 'entry.png');
copyFileSync(source, destination);
console.error(
  `copied ${format} ${dimensions.width}x${dimensions.height}, ${image.length} bytes -> ${destination}`,
);
