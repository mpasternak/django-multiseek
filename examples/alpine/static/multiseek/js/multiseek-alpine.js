/* multiseek-alpine.js — Variant 3 (Bootstrap 5 + Alpine.js, no jQuery).
 *
 * Reimplements the django-multiseek widget tree as a single Alpine.js
 * component. The reactive `frames` state IS the form_data tree; serialize()
 * is a thin walk that produces the wire format multiseek expects:
 *
 *     [prev_op, ...elements]
 *
 * where each element is either:
 *   - a field object: { field, operator, value, prev_op }
 *   - a nested frame array following the same shape
 *
 * Wire-format reference: docs/FRONTENDS.md in this repository.
 */

(function () {
    "use strict";

    /* ---- helpers ----------------------------------------------------- */

    function readJSON(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            console.error("multiseek: failed to parse JSON from #" + id, e);
            return null;
        }
    }

    let _uidCounter = 0;
    function nextUid() {
        _uidCounter += 1;
        return _uidCounter;
    }

    /* ---- Alpine root component --------------------------------------- */

    function multiseekForm() {
        return {
            /* config (filled by init()) */
            fields: [],
            ops: {},
            types: {},
            value_lists: {},
            autocompletes: {},
            removeLastFieldMessage: "",
            and_label: "and",
            or_label: "or",
            orderingPrefix: "order_",
            reportTypeKey: "_ms_report_type",
            savedForms: [],
            userCanSave: false,

            /* ----- reactive state ----- */
            // frames is a list. The root frame is frames[0]; nested frames are
            // child elements with kind === "frame". This mirrors the form_data
            // shape, but with kind tags so Alpine can render conditionally.
            frames: [],
            ordering: [], // [{ field: "0", desc: false }, ...]
            reportType: "0",

            /* ----- lifecycle ----- */
            init() {
                this.fields = readJSON("ms-fields") || [];
                this.ops = readJSON("ms-ops") || {};
                this.types = readJSON("ms-types") || {};
                this.value_lists = readJSON("ms-value-lists") || {};
                this.autocompletes = readJSON("ms-autocompletes") || {};

                const config = readJSON("ms-config") || {};
                this.removeLastFieldMessage =
                    config.removeLastFieldMessage ||
                    "The ability to remove the last field has been disabled.";
                this.and_label = config.and_label || "and";
                this.or_label = config.or_label || "or";
                this.orderingPrefix = config.orderingPrefix || "order_";
                this.reportTypeKey = config.reportTypeKey || "_ms_report_type";
                this.savedForms = config.savedForms || [];
                this.userCanSave = !!config.userCanSave;

                // Try to hydrate from existing session form_data first.
                // Falls back to an empty root frame + one default field if the
                // session is empty or unparseable.
                const formDataEl = document.getElementById("ms-form-data");
                let hydrated = false;
                if (formDataEl && formDataEl.textContent.trim()) {
                    try {
                        const formData = JSON.parse(formDataEl.textContent);
                        if (Array.isArray(formData) && formData.length > 0) {
                            this.frames.push(this._hydrateFrame(formData, true));
                            hydrated = true;
                        }
                    } catch (e) {
                        // fall through to empty-form init
                    }
                }
                if (!hydrated) {
                    const rootFrame = this._makeFrame();
                    this.frames.push(rootFrame);
                    if (config.initializeEmpty !== false) {
                        this.addField(rootFrame);
                    }
                }

                // initialize ordering state (defaults: field=0, desc=false)
                // The template uses ordering[idx].field / .desc.
                const orderingBoxes = document.querySelectorAll(
                    "[id^='order_'][id$='_dir']",
                );
                this.ordering = Array.from(orderingBoxes).map(() => ({
                    field: "0",
                    desc: false,
                }));
            },

            /* ----- i18n stub: pass-through; could read django jsi18n later ----- */
            t(s) {
                if (s === "and") return this.and_label;
                if (s === "or") return this.or_label;
                if (s === "and not") return "and not";
                return s;
            },

            /* ----- factories ----- */
            _makeFrame() {
                return {
                    uid: nextUid(),
                    kind: "frame",
                    prev_op: "and",
                    elements: [],
                };
            },

            /* ----- hydration from multiseek form_data ----- */
            _hydrateField(elem, isFirst) {
                const t = this.types[elem.field] || "string";
                const f = {
                    uid: nextUid(),
                    kind: "field",
                    field: elem.field || (this.fields[0] || ""),
                    operator: elem.operator || "",
                    value: elem.value || "",
                    value_min: null,
                    value_max: null,
                    prev_op: isFirst ? "and" : (elem.prev_op || "and"),
                };
                // Split JSON-encoded range/date values back into per-input bindings.
                if (t === "range" && elem.value) {
                    try {
                        const parsed = JSON.parse(elem.value);
                        if (Array.isArray(parsed) && parsed.length === 2) {
                            f.value_min = parsed[0];
                            f.value_max = parsed[1];
                        }
                    } catch (e) { /* leave value_min/_max null */ }
                } else if (t === "date" && elem.value) {
                    try {
                        const parsed = JSON.parse(elem.value);
                        if (Array.isArray(parsed)) {
                            f.value = parsed[0] || "";
                            if (parsed.length > 1) f.value_max = parsed[1];
                        }
                    } catch (e) { /* leave as-is */ }
                }
                return f;
            },

            _hydrateFrame(arr, isRoot) {
                // arr is a multiseek form_data list: [prev_op, elem_1, elem_2, ...]
                const frame = {
                    uid: nextUid(),
                    kind: "frame",
                    prev_op: isRoot ? "and" : (arr[0] || "and"),
                    elements: [],
                };
                for (let i = 1; i < arr.length; i++) {
                    const elem = arr[i];
                    if (Array.isArray(elem)) {
                        frame.elements.push(this._hydrateFrame(elem, false));
                    } else if (elem && typeof elem === "object") {
                        frame.elements.push(this._hydrateField(elem, i === 1));
                    }
                }
                return frame;
            },

            _makeField(opts) {
                opts = opts || {};
                const fieldLabel = opts.field || (this.fields[0] || "");
                const operatorList = this.ops[fieldLabel] || [];
                const operator = opts.operator || (operatorList[0] || "");
                const fieldType = this.types[fieldLabel] || "string";

                const f = {
                    uid: nextUid(),
                    kind: "field",
                    field: fieldLabel,
                    operator: operator,
                    value: opts.value !== undefined ? opts.value : "",
                    value_min: opts.value_min !== undefined ? opts.value_min : null,
                    value_max: opts.value_max !== undefined ? opts.value_max : null,
                    prev_op: opts.prev_op || "and",
                };

                // Sensible defaults for non-string widgets
                if (fieldType === "value-list") {
                    const vl = this.value_lists[fieldLabel] || [];
                    f.value = opts.value !== undefined ? opts.value : (vl[0] || "");
                }
                return f;
            },

            /* ----- mutations ----- */
            addField(frame) {
                frame.elements.push(this._makeField());
            },

            addFrame(parentFrame) {
                const nested = this._makeFrame();
                // a nested frame gets one initial field, matching the legacy
                // jQuery behavior in multiseek.js: addFrameViaButton.
                nested.elements.push(this._makeField());
                parentFrame.elements.push(nested);
            },

            addFieldToFrame(nestedFrame) {
                nestedFrame.elements.push(this._makeField());
            },

            removeField(frame, elem) {
                // Don't allow removing the very last field of the root frame.
                const rootFrame = this.frames[0];
                if (
                    frame === rootFrame &&
                    rootFrame.elements.length === 1 &&
                    rootFrame.elements[0] === elem
                ) {
                    alert(this.removeLastFieldMessage);
                    return;
                }
                const idx = frame.elements.indexOf(elem);
                if (idx !== -1) frame.elements.splice(idx, 1);
            },

            removeFrame(parentFrame, nestedFrame) {
                const idx = parentFrame.elements.indexOf(nestedFrame);
                if (idx !== -1) parentFrame.elements.splice(idx, 1);
            },

            /* ----- lookups for the templates ----- */
            opsFor(fieldLabel) {
                return this.ops[fieldLabel] || [];
            },
            typeFor(fieldLabel) {
                return this.types[fieldLabel] || "string";
            },
            valueListFor(fieldLabel) {
                return this.value_lists[fieldLabel] || [];
            },

            isDateRangeOp(elem) {
                // Mirrors multiseek.js: idx > 5 means a range-style date op
                // (e.g. "between X and Y"). The first 6 operators are scalar.
                const list = this.opsFor(elem.field);
                const idx = list.indexOf(elem.operator);
                return idx > 5;
            },

            /* ----- type/operator change hooks ----- */
            onFieldChange(elem) {
                // when field changes, default operator + value reset
                const list = this.opsFor(elem.field);
                elem.operator = list[0] || "";
                this._resetValueForType(elem);
            },
            onOperatorChange(elem) {
                // for date range support: clear the extra field if no longer applicable
                if (this.typeFor(elem.field) === "date" && !this.isDateRangeOp(elem)) {
                    elem.value_max = null;
                }
            },
            _resetValueForType(elem) {
                const t = this.typeFor(elem.field);
                if (t === "integer" || t === "decimal" || t === "range") {
                    elem.value = "";
                    elem.value_min = null;
                    elem.value_max = null;
                } else if (t === "value-list") {
                    const vl = this.valueListFor(elem.field);
                    elem.value = vl[0] || "";
                } else if (t === "date") {
                    elem.value = "";
                    elem.value_max = null;
                } else {
                    elem.value = "";
                }
            },

            /* ----- flatpickr bootstrap (vanilla, no jQuery) ----- */
            initFlatpickr(el) {
                if (typeof window.flatpickr === "function") {
                    window.flatpickr(el, { dateFormat: "Y-m-d" });
                }
            },

            /* ----- description preview for nested-frame sub-elements ----- */
            describeSub(sub, idx) {
                if (sub.kind === "field") {
                    const prev = idx > 0 ? (this.t(sub.prev_op) || "") : "";
                    return `${prev} ${sub.field} ${sub.operator} ${sub.value || ""}`.trim();
                }
                return "(nested frame)";
            },

            /* ----- serialization to wire format ----- */
            // Walk the reactive frames tree and produce the `[prev_op, ...]`
            // shape multiseek's Python core expects.
            _serializeField(elem, isFirst) {
                const t = this.typeFor(elem.field);
                let value;
                if (t === "range") {
                    // wire format: JSON-stringified [min, max]
                    value = JSON.stringify([
                        parseInt(elem.value_min, 10),
                        parseInt(elem.value_max, 10),
                    ]);
                } else if (t === "date") {
                    const arr = [elem.value || ""];
                    if (elem.value_max) arr.push(elem.value_max);
                    value = JSON.stringify(arr);
                } else if (t === "integer") {
                    value = parseInt(elem.value, 10);
                    if (isNaN(value)) value = null;
                } else if (t === "decimal") {
                    const f = parseFloat(elem.value);
                    value = isNaN(f) ? null : f.toFixed(3);
                } else {
                    value = elem.value;
                }
                return {
                    field: elem.field,
                    operator: elem.operator,
                    value: value === null || value === undefined ? "" : value,
                    prev_op: isFirst ? null : elem.prev_op,
                };
            },

            _serializeFrame(frame, isRoot) {
                const out = [];
                // First slot of a frame's array is the prev_op of the FRAME
                // itself (null for the root, otherwise "and"/"or"/"andnot").
                out.push(isRoot ? null : frame.prev_op);
                for (let i = 0; i < frame.elements.length; i++) {
                    const elem = frame.elements[i];
                    if (elem.kind === "frame") {
                        out.push(this._serializeFrame(elem, false));
                    } else {
                        out.push(this._serializeField(elem, i === 0));
                    }
                }
                return out;
            },

            serialize() {
                return this._serializeFrame(this.frames[0], true);
            },

            formAsJSON() {
                const orderingObj = {};
                this.ordering.forEach((o, i) => {
                    orderingObj[this.orderingPrefix + i] = o.field;
                    if (o.desc) orderingObj[this.orderingPrefix + i + "_dir"] = "1";
                });
                return JSON.stringify({
                    form_data: this.serialize(),
                    ordering: orderingObj,
                    report_type: this.reportType,
                });
            },

            /* ----- network actions (vanilla fetch, no jQuery) ----- */

            sendQuery() {
                const json = this.formAsJSON();
                const form = document.createElement("form");
                form.method = "post";
                form.action = "./results/";
                form.target = "list_frame";

                const jsonInput = document.createElement("input");
                jsonInput.name = "json";
                jsonInput.value = json;
                form.appendChild(jsonInput);

                const csrfInput = document.createElement("input");
                csrfInput.name = "csrfmiddlewaretoken";
                csrfInput.value = window.multiseekCSRFToken || "";
                form.appendChild(csrfInput);

                document.body.appendChild(form);
                form.submit();
                form.remove();
            },

            resetForm() {
                window.location.href = "./reset/";
            },

            loadForm(pk) {
                if (!pk) return;
                if (confirm("Are you sure you want to load selected form?")) {
                    window.location.href = "./load_form/" + pk;
                }
            },

            async saveForm() {
                const name = prompt("Form name?");
                if (name == null) return;
                if (name === "") {
                    alert("Form name must not be empty.");
                    return;
                }
                const isPublic = confirm(
                    "Should the form be available for every user of this website?",
                );

                const sendSave = async (overwrite) => {
                    const body = new URLSearchParams();
                    body.append("json", this.formAsJSON());
                    body.append("name", name);
                    body.append("public", isPublic ? "true" : "false");
                    body.append("overwrite", overwrite ? "true" : "false");
                    const resp = await fetch("./save_form/", {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": window.multiseekCSRFToken || "",
                            "Content-Type":
                                "application/x-www-form-urlencoded",
                        },
                        body: body.toString(),
                        credentials: "same-origin",
                    });
                    return resp.json();
                };

                try {
                    let data = await sendSave(false);
                    if (data.result === "overwrite-prompt") {
                        if (
                            confirm(
                                "There is already a form with such name in the database. Overwrite?",
                            )
                        ) {
                            data = await sendSave(true);
                        } else {
                            return;
                        }
                    }
                    if (data.result === "saved") {
                        alert("Form was saved.");
                        this.savedForms.push({ pk: data.pk, label: name });
                    } else {
                        alert(data.result);
                    }
                } catch (e) {
                    console.error(e);
                    alert("There was a server-side error. The form was NOT saved.");
                }
            },
        };
    }

    /* ---- register with Alpine ---------------------------------------- */

    document.addEventListener("alpine:init", function () {
        window.Alpine.data("multiseekForm", multiseekForm);
    });

    // Expose for debugging
    window.multiseekFormFactory = multiseekForm;
})();
