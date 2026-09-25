import assert from "node:assert/strict";
import test from "node:test";

import { JSDOM } from "jsdom";

import { createWizardDraftStorage } from "../src/js/modules/wizard-draft-storage.js";

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    removeItem: (key) => values.delete(key),
    setItem: (key, value) => values.set(key, value),
  };
}

function wizardForm() {
  return new JSDOM(`
    <form>
      <input name="examination_date" value="2026-09-25">
      <input name="carat_weight" value="1.25">
      <select name="shape"><option value=""></option><option value="round" selected>Round</option></select>
      <input name="expert_comment" value="Visible inclusion">
      <input name="plotting_image" type="file">
    </form>
  `).window.document.querySelector("form");
}

test("wizard draft storage keeps serializable form values isolated per user", () => {
  const storage = memoryStorage();
  const form = wizardForm();
  const ownerStorage = createWizardDraftStorage({ userId: 2, storage });

  assert.equal(ownerStorage.save(form, 2), true);
  const draft = ownerStorage.read();

  assert.equal(draft.current_step, 2);
  assert.equal(draft.values.carat_weight, "1.25");
  assert.equal(draft.values.plotting_image, undefined);
  assert.equal(createWizardDraftStorage({ userId: 3, storage }).read(), null);
});

test("wizard draft storage restores values and discards an empty or invalid draft", () => {
  const storage = memoryStorage();
  const form = wizardForm();
  const drafts = createWizardDraftStorage({ userId: 2, storage });
  drafts.save(form, 3);

  form.elements.namedItem("carat_weight").value = "";
  form.elements.namedItem("shape").value = "";
  form.elements.namedItem("expert_comment").value = "";
  drafts.restore(form, drafts.read());

  assert.equal(form.elements.namedItem("carat_weight").value, "1.25");
  assert.equal(form.elements.namedItem("shape").value, "round");
  assert.equal(form.elements.namedItem("expert_comment").value, "Visible inclusion");

  storage.setItem("diamant-id:wizard-draft:v1:user:2", JSON.stringify({ schema_version: 999, user_id: 2, current_step: 1, values: { shape: "round" } }));
  assert.equal(drafts.read(), null);
  assert.equal(storage.getItem("diamant-id:wizard-draft:v1:user:2"), null);
});
