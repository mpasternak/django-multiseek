/* Bootstrap 5 + jQuery flavor of multiseek.js.
 *
 * This file is intentionally a near-clone of multiseek/static/multiseek/js/multiseek.js
 * (the bundled Foundation 6 version). The only changes are:
 *   - Foundation grid classes ("grid-x", "cell", "large-N", "small-N",
 *     "row collapse", "columns") are swapped for Bootstrap 5 classes
 *     ("row", "col", "col-N").
 *   - Foundation button classes ("button", "button alert") are swapped for
 *     Bootstrap 5 ("btn btn-primary", "btn btn-danger").
 *   - foundation-datepicker (.fdatepicker) is replaced by flatpickr.
 *
 * The widget tree (multiseekFrame, multiseekField, ...) and the JSON
 * serialization logic are unchanged.
 */

if (typeof String.prototype.startsWith != 'function') {
    String.prototype.startsWith = function (str) {
        return this.indexOf(str) == 0;
    };
}

if (window.multiseek == undefined) window.multiseek = {};

multiseek = {
    frame_counter: 0,
    field_counter: 0,
    autocomplete_counter: 0,
    LOAD_FORM_URL: './load_form/',
    SAVE_FORM_URL: './save_form/',

    widgetMapping: {
        'string': 'multiseekStringValue',
        'integer': 'multiseekIntegerValue',
        'decimal': 'multiseekDecimalValue',
        'value-list': 'multiseekValueListValue',
        'date': 'multiseekDateValue',
        'autocomplete': 'multiseekAutocompleteValue',
        'range': 'multiseekRangeValue'
    }
};

function installDatePicker(element) {
    /* Bootstrap variant: use flatpickr instead of foundation-datepicker. */
    if (typeof flatpickr !== 'undefined') {
        flatpickr(element[0], {
            dateFormat: (typeof multiseekDateFormat !== 'undefined') ? multiseekDateFormat : 'Y-m-d',
            weekNumbers: false,
            allowInput: true
        });
    } else if (element.datepicker) {
        /* fallback: jQuery UI datepicker */
        element.datepicker($.datepicker.regional[djangoLanguageCode]);
    }
}


$.widget("multiseek.multiseekBase", {
    // Both field and frame widgets share common elements

    getPrevOperationDOM: function () {
        return $("<select />")
            .attr("id", "prev-op")
            .addClass("multiseek-prev-op form-select form-select-sm")
            .append([
                $("<option/>").html(gettext("and")).attr("value", "and"),
                $("<option/>").html(gettext("or")).attr("value", "or"),
                $("<option/>").html(gettext("and not")).attr("value", "andnot")
            ])
    },

    prevOperation: function (action) {
        var ph = this.element.find("#prev-op-placeholder");
        if (action == "enable") {
            if (ph.children().length == 0)
                ph.first().append(this.getPrevOperationDOM());
        } else if (action == "disable") {

            ph.first().fadeOut(function () {
                /* In the Bootstrap variant the prev-op slot is a col-2; the
                 * sibling type-select slot is col-3 when prev-op is hidden,
                 * col-2 otherwise. We keep this behavior approximately
                 * matching the original Foundation logic. */
                var nxt = ph.parent().next();
                if (nxt.hasClass("col-2")) {
                    nxt.removeClass("col-2");
                    nxt.addClass("col-3");
                    ph.parent().hide();
                }

                var nxt2 = ph.first().next();
                if (nxt2.hasClass("col-11")) {
                    nxt2.removeClass("col-11");
                    nxt2.addClass("col-12");
                }

                ph.first().remove();
            });

        } else
            return ph.first().children("#prev-op");
    },

    getPrevOperationValue: function () {
        var prev_op = this.prevOperation();
        if (prev_op)
            return prev_op.val();

        return null;
    },

    enableOrDisablePrevOp: function () {
        if (this.element.prev().length) {
            this.prevOperation("enable");
            return;
        }
        this.prevOperation("disable");
    }


});

$.widget("multiseek.multiseekBaseValue", {
    _create: function () {

    },

    update: function (value, index) {
        // when operation was changed
    }
});

$.widget("multiseek.multiseekStringValue", $.multiseek.multiseekBaseValue, {
    _create: function () {
        this.element.append(
            $('<input/>')
                .attr("type", "text")
                .attr("name", "value")
                .attr("id", "value")
                .attr("size", "30")
                .addClass("form-control form-control-sm")
        );
    },

    getValue: function () {
        return this.element.children().first().val();
    },

    setValue: function (value) {
        return this.element.children().first().val(value);
    }

});

$.widget("multiseek.multiseekIntegerValue", $.multiseek.multiseekStringValue, {
    getValue: function () {
        return parseInt(this.element.children().first().val());
    }
});

$.widget("multiseek.multiseekDecimalValue", $.multiseek.multiseekStringValue, {
    getValue: function () {
        return parseFloat(this.element.children().first().val()).toFixed(3);
    }
});

$.widget("multiseek.multiseekRangeValue", $.multiseek.multiseekBaseValue, {
    _create: function () {
        this.element.append(
            $("<div/>")
                .addClass("row g-1")
                .append([
                    $("<div/>")
                        .addClass("col-1 multiseek-range-field-label")
                        .text(gettext("from")),

                    $("<div/>")
                        .addClass("col-5")
                        .append([
                            $("<input type=text id=value_min size=4 class='form-control form-control-sm' />")]),

                    $("<div/>")
                        .addClass("col-1 multiseek-range-field-label")
                        .text(gettext("to")),

                    $("<div/>")
                        .addClass("col-5")
                        .append([
                            $("<input type=text id=value_max size=4 class='form-control form-control-sm' />")])
                ])
        );
    },

    getValue: function () {
        var min = this.element.find("input#value_min").val();
        var max = this.element.find("input#value_max").val();
        return JSON.stringify([parseInt(min), parseInt(max)]);

    },

    setValue: function (value) {
        var value = $.parseJSON(value);
        this.element.find("input#value_min").val(value[0]);
        this.element.find("input#value_max").val(value[1]);
    }
});


$.widget("multiseek.multiseekAutocompleteValue", $.multiseek.multiseekBaseValue, {
    _create: function () {
        this.element.append(
            $("<div/>")
                .addClass("row")
                .append([
                    $("<select/>")
                        .attr("data-autocomplete-light-url", this.options.url)
                        .attr("data-autocomplete-light-function", "select2")
                        .attr("data-autocomplete-light-language", djangoLanguageCode)
                        .attr("data-html", "")
                        .attr("data-placeholder", gettext("Click and begin typing to look up..."))
                        .addClass("form-select form-select-sm")
                ])
        );
    },

    getValue: function () {
        return this.element.find("select").val();
    },

    setValue: function (value) {
        value = $.parseJSON(value);
        var select = this.element.find("select");
        var option = new Option(value[1], value[0], true, true);
        select.append(option).trigger('change');
    }
});


$.widget("multiseek.multiseekValueListValue", $.multiseek.multiseekBaseValue, {
    _create: function () {
        var element = $('<select/>')
            .attr("class", "values form-select form-select-sm")
            .attr("name", "value_list")
            .attr("id", "value");

        value_lists[this.options.fieldName].forEach(function (v) {
            element.append($('<option/>').val(v).html(v));
        });
        this.element.append(element);
    },

    setValue: function (value) {
        this.element.find("select[name=value_list]").val(value);
    },

    getValue: function () {
        return this.element.find("select[name=value_list]").val();
    }
});

$.widget("multiseek.multiseekDateValue", $.multiseek.multiseekBaseValue, {
    _create: function () {
        var element = $('<input/>')
            .attr("type", "text")
            .attr("name", "value")
            .attr("id", "value")
            .attr("placeholder", gettext('today'))
            .attr("size", "10")
            .addClass("form-control form-control-sm flatpickr");

        installDatePicker(element);

        this.element.append(
            $("<div/>")
                .addClass("row g-1")
                .append([
                    $("<div/>")
                        .addClass("col-5")
                        .append([element])
                ])
        );
    },

    setValue: function (value) {
        value = $.parseJSON(value);
        this.element.find("input[name=value]").val(value[0]);
        if (value.length > 1)
            this.element.find("input#value_max").val(value[1]);
    },

    getValue: function () {
        var ret = [this.element.find("input[name=value]").val()];
        this.element.find("input#value_max").each(
            function (no, elem) {
                ret.push($(elem).val());
            }
        )
        return JSON.stringify(ret);
    },

    update: function (value, idx) {
        var row = this.element.children().eq(0);

        if (idx > 5) {
            // range
            if (row.children().length == 1) {
                // add extra field

                var element = $("<input/>")
                    .attr("type", "text")
                    .attr("id", "value_max")
                    .attr("placeholder", gettext('today'))
                    .attr("size", "10")
                    .addClass("form-control form-control-sm flatpickr");

                installDatePicker(element);
                row.append([
                    $("<div/>")
                        .addClass("col-2 text-center")
                        .append($("<span/>").text("—")),
                    $("<div/>")
                        .addClass("col-5")
                        .append([element])
                ]);

            }
        } else {
            // single field
            if (row.children().length > 1) {
                // remove extra field
                row.children().eq(1).remove();
                row.children().eq(1).remove();
            }
        }
    }
});


$.widget("multiseek.multiseekField", $.multiseek.multiseekBase, {

    _create: function () {
        this.typeSelect().change($.proxy(this.typeSelectChanged, this));
        this.opSelect().change($.proxy(this.opSelectChanged, this));

        this.setTypeSelectValues();
        this.enableOrDisablePrevOp();
    },

    typeSelect: function () {
        return this.element.find("#type");
    },

    typeSelectChanged: function (evt) {
        this.initializeValueWidget();
        this.updateOpsSelect();
    },

    getFieldType: function () {
        return types[this.typeSelect().val()];
    },

    getFieldName: function () {
        return this.typeSelect().val();
    },

    getWidgetType: function () {
        return multiseek.widgetMapping[this.getFieldType()];
    },

    setTypeSelectValues: function () {
        var select = this.typeSelect();
        select.children().remove();
        fields.forEach(function (value) {
            select.append($('<option/>').val(value).html(value));
        });
        this.typeSelect().change();
    },


    opSelect: function () {
        return this.element.find("#op");
    },

    opSelectChanged: function (evt) {
        this.updateValueWidget();
    },

    updateOpsSelect: function () {
        var ops_select = this.opSelect();
        ops_select.children().remove();

        if (!ops[this.getFieldName()])
            return;

        ops[this.getFieldName()].forEach(function (value) {
            ops_select.append($('<option/>').val(value).html(value));
        });
        ops_select.change();
    },

    getFieldOp: function () {
        return ops[this.opSelect().val()];
    },

    valueElement: function () {
        return this.element.find("#value-placeholder").children().first();
    },

    initializeValueWidget: function () {
        var p = this.element.find("#value-placeholder");
        try {
            p[this.getWidgetType()]("destroy");
        } catch (Error) {
        }

        p.children().remove();
        p.append("<span/>");
        p = $(p.children()[0]);

        switch (this.getFieldType()) {
            case 'autocomplete':
                p.multiseekAutocompleteValue(
                    {'url': autocompletes[this.getFieldName()]});
                break;

            default:
                p[this.getWidgetType()]({'fieldName': this.getFieldName()});
                break;
        }
    },

    updateValueWidget: function () {
        this.valueElement()[this.getWidgetType()]('update',
            this.opSelect().val(),
            this.opSelect()[0].selectedIndex);
    },

    setType: function (type) {
        this.typeSelect().val(type);
        this.typeSelect().change();
    },

    setOperation: function (operation) {
        this.opSelect().val(operation);
        this.opSelect().change();
    },

    setValueWidget: function (value) {
        return this.valueElement()[this.getWidgetType()]('setValue', value);
    },

    getValue: function () {
        return this.valueElement()[this.getWidgetType()]('getValue');
    },

    serialize: function () {
        return {
            'field': this.getFieldName(),
            'operator': this.opSelect().val(),
            'value': this.getValue(),
            'prev_op': this.getPrevOperationValue()
        };
    },

    setValue: function (type, operation, value, prevOp) {
        this.setType(type);
        this.setOperation(operation);
        this.setValueWidget(value);
        this.prevOperation().val(prevOp);
    }

});

$.multiseek.multiseekField.prototype.options = {
    'type': 0,
    'operation': 0,
    'value': null
};

$.widget("multiseek.multiseekFrame", $.multiseek.multiseekBase, {

    makeFrameDOM: function (element) {
        var div = $("<div/>")
            .addClass("col-1")
            .attr("id", "prev-op-placeholder");

        var fieldset = $("<fieldset />")
            .addClass("multiseek-fieldset col-11 border rounded p-2 mb-2")
            .append([

                $("<div/>")
                    .attr("id", "field-list")
                    .addClass("col"),

                $("<div/>")
                    .addClass("btn-group mt-2")
                    .attr("role", "group")
                    .append([

                        $("<button/>")
                            .attr("id", "add_field")
                            .attr("type", "button")
                            .addClass("btn btn-primary btn-sm")
                            .addClass("multiseek-add-field-button")
                            .click($.proxy(function (evt) {
                                evt.preventDefault();
                                this.addFieldViaButton();
                            }, this))
                            .append([
                                $("<span/>").addClass("me-1").text("+"),
                                gettext("Add field")
                            ]),
                        $("<button/>")
                            .attr("id", "add_frame")
                            .attr("type", "button")
                            .addClass("btn btn-primary btn-sm")
                            .addClass("multiseek-add-frame-button")
                            .click($.proxy(function (evt) {
                                    evt.preventDefault();
                                    this.addFrameViaButton();
                                }, this
                            ))
                            .append([
                                $("<span/>").addClass("me-1").text("+"),
                                gettext("Add frame")
                            ])
                    ])
            ]);

        if (!multiseek.frame_counter) {
            div = "";
            fieldset.removeClass("col-11").addClass("col-12");
        }

        element
            .attr("id", "frame-" + multiseek.frame_counter)
            .attr("class", "multiseekFrame row g-1 my-2")
            .css("display", "flex")
            .append([div, fieldset]);
    },

    _create: function () {
        this.makeFrameDOM(this.element);
        multiseek.frame_counter++;
    },


    fieldList: function () {
        return this.element.children("fieldset").children("#field-list");
    },

    noFields: function () {
        return this.fieldList().children().length;
    },

    empty: function () {
        return this.noFields() == 0;
    },

    removeFrame: function (id) {
        var for_removal = this.fieldList().find("#" + id);

        var next = for_removal.next();

        var that = this;

        for_removal.slideUp(function () {
            for_removal.remove();

            next.multiseekBase().multiseekBase("enableOrDisablePrevOp");

            if (that.empty() && that.element.attr("id") != "frame-0")
                that.removeSelf();
        });

    },

    parentFrame: function () {
        return this.element.parent().parent().parent();
    },

    removeSelf: function () {
        this.parentFrame().multiseekFrame(
            "removeFrame", this.element.attr("id"));
    },

    removeField: function (evt) {
        var fld = $("#" + $(evt.target).data("for-field"));

        if (this.noFields() == 1 && this.element.attr("id") == "frame-0") {
            alert(last_field_remove_message);
            return;
        }

        var next = fld.next();

        var that = this;
        fld.slideUp(null, function () {
            fld.remove();
            next.multiseekBase().multiseekBase("enableOrDisablePrevOp");

            if (that.empty())
                that.removeSelf();

        });
    },

    getFieldDOM: function (id, has_elements) {
        var div = $("<div/>")
            .addClass("col-1")
            .append(
                $('<div/>').attr("id", "prev-op-placeholder")
            );

        var oplen = "col-2";
        if (!has_elements) {
            div = "";
            oplen = "col-3";
        }

        return $("<field/>")
            .addClass("row g-1 align-items-center mb-1")
            .attr("id", id)
            .append([
                div,
                $("<div/>")
                    .addClass(oplen)
                    .append(
                        $("<select/>")
                            .attr("id", "type")
                            .addClass("multiseek-type form-select form-select-sm")
                    ),
                $("<div/>")
                    .addClass("col-2")
                    .append(
                        $("<select/>")
                            .attr("id", "op")
                            .addClass("multiseek-op form-select form-select-sm")
                    ),
                $("<div/>")
                    .addClass("col-6")
                    .attr("id", "value-placeholder"),

                $("<div/>")
                    .addClass("col-1")
                    .append(
                        $("<button/>")
                            .html("&times;")
                            .attr("id", "close-button")
                            .attr("type", "button")
                            .addClass('btn btn-danger btn-sm')
                            .data("for-field", id)
                            .click($.proxy(function (evt) {
                                    evt.preventDefault();
                                    this.removeField(evt);
                                }, this
                            )))
            ]);
    },

    addField: function (type, operation, value, op) {
        var id = "field-" + multiseek.field_counter;
        var has_elements = this.fieldList().children().length;
        var elem;

        elem = this.getFieldDOM(id, has_elements);
        this.fieldList().append(elem);
        $(elem).hide();
        $(elem).slideDown();

        var fld = $("#" + id);
        fld.multiseekField();
        if (type && operation)
            fld.multiseekField("setValue", type, operation, value, op);
        multiseek.field_counter++;

    },

    addFieldViaButton: function () {
        this.addField();

    },

    addFrame: function (prevOpValue) {
        var id = "frame-" + multiseek.frame_counter;
        var has_elements = this.fieldList().children().length;
        this.fieldList().append(
            $("<div/>")
                .attr("id", id)
        );
        var fr = $("#" + id);
        fr.hide();
        fr.multiseekFrame();
        fr.slideDown();
        if (has_elements) {
            fr.multiseekFrame("prevOperation", "enable");
            if (prevOpValue)
                fr.multiseekFrame("prevOperation").val(prevOpValue);
        }

        return fr;
    },

    addFrameViaButton: function () {
        var f = this.addFrame("and");
        f.multiseekFrame("addField");

    },

    serialize: function (level) {
        var ret = [];

        if (level === undefined)
            level = 0;

        if (level != 0)
            ret.push(this.getPrevOperationValue());
        else
            ret.push(null);

        this.fieldList().children().each($.proxy(function (no, elem) {
            if ($(elem).attr("id").startsWith("field")) {
                ret.push($(elem).multiseekField("serialize", level + 1));
                return;
            }
            ret.push($(elem).multiseekFrame("serialize", level + 1));
        }, this));

        return ret;
    }
});

function formOrdering() {
    var ret = {};

    $(".multiseek-ordering").each(function (no, elem) {
        var pn = "order_" + no;
        ret[pn] = $(elem).find(":selected").val();

        pn = pn + "_dir";
        if ($("input[name=" + pn + "]:checked").length)
            ret[pn] = "1";
    });
    return ret;
}

function formReportType() {
    var sel = $("select[name=_ms_report_type]");
    if (sel.length) {
        return sel.val();
    }
}

function formAsJSON() {
    return JSON.stringify(
        {
            'form_data': $("#frame-0").multiseekFrame("serialize"),
            'ordering': formOrdering(),
            'report_type': formReportType()
        });
}

function submitEvent(button) {
    var value = formAsJSON();

    var form = $("<form/>").attr({
        method: "post",
        action: "./results/",
        target: "list_frame"
    })
        .append($("<input/>").attr('name', 'json').attr({"value": value}))
        .append($("<input/>").attr('name', 'csrfmiddlewaretoken')
            .attr({"value": window.multiseekCSRFToken || ''}));

    $("body").append(form);

    form.submit().remove();
}

function resetForm(button) {
    location.href = './reset/';
}

function updateFormSelector(pk, value) {
    if ($("#formsSelector option[value=" + pk + "]").length == 0)
        $("#formsSelector").append(
            $("<option/>").val(pk).html(value)
        );
    $("#formsSelector").show();
}

function saveForm(button) {
    var dct = {
        'json': formAsJSON(),
        'name': prompt(gettext("Form name?")),
        'csrfmiddlewaretoken': window.multiseekCSRFToken || ''
    };

    if (dct.name == null)
        return;

    if (dct.name == '') {
        alert(gettext("Form name must not be empty."));
        return;
    }

    setTimeout(function () {
        saveFormRest1(dct);
    }, 500);
}

function saveFormRest1(dct) {
    dct.public = confirm(
        gettext("Should the form be available for every user of this website?"));
    setTimeout(function () {
        saveFormRest2(dct);
    }, 500);
}

function saveFormRest2(dct) {
    var url = multiseek.SAVE_FORM_URL;
    var error = gettext('There was a server-side error. The form was NOT saved.');
    var saved = gettext('Form was saved.');
    var form_exists = gettext('There is already a form with such name in the database. Overwrite?');

    $.post(url, dct,
        function (data, textStatus, jqXHR) {
            if (textStatus == 'success') {

                if (data.result == 'saved') {
                    updateFormSelector(data.pk, dct['name']);
                    setTimeout(function () {
                        alert(saved);
                    }, 500);
                } else if (data.result == 'overwrite-prompt') {
                    if (confirm(form_exists)) {
                        dct['overwrite'] = true;
                        $.post(url, dct, function (data, textStatus, jqXHR) {
                            if (textStatus == 'success') {
                                if (data.result == 'saved') {
                                    setTimeout(function () {
                                        alert(saved);
                                    }, 500);
                                    updateFormSelector(data.pk, dct['name']);
                                } else
                                    alert(data.result);
                            } else
                                alert(error);
                        }).error(function () {
                            alert(error);
                        });
                    }
                } else
                    alert(data.result);

            } else
                alert(error);
        }
    ).fail(function () {
        alert(error);
    });
}

function loadForm(select) {
    if (confirm(gettext("Are you sure you want to load selected form?")))
        location.href = multiseek.LOAD_FORM_URL + $(select).val();
    $(select).val('');
}

window.multiseek.removeFromResults = function (id) {
    var elem = $("#multiseek-row-" + id).children(".multiseek-element");
    var deco = elem.css("text-decoration");

    var css_after = 'line-through';
    var url = '../remove-from-results/' + id;

    if (deco.startsWith("line-through")) {
        css_after = 'none';
        url = '../remove-from-removed-results/' + id;
    }

    $.get(url, function (data) {
        elem.css("text-decoration", css_after);
    });
};
