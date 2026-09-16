import assert from "node:assert/strict";
import test from "node:test";

import { backendPath } from "../src/index.ts";

test("maps only the public CREST prefix to the backend root", () => {
  assert.equal(backendPath("/crest"), "/");
  assert.equal(backendPath("/crest/"), "/");
  assert.equal(backendPath("/crest/api/capabilities"), "/api/capabilities");
  assert.equal(backendPath("/crestful"), null);
  assert.equal(backendPath("/"), null);
});
