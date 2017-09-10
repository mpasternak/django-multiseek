
if (typeof String.prototype.startsWith != 'function') {
    // see below for better implementation!
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
      if (element.fdatepicker) {
          /* Use foundation date picker if available */
          element.fdatepicker({
              format: multiseekDateFormat,
              weekStart: multiseekDateWeekStart,
              language: djangoLanguageCode
          });
      } else {
          /* Use JQuery datepicker if available */
          element.datepicker($.datepicker.regional[djangoLanguageCode]);
      }
}


$.widget("multiseek.multiseekBase", {
    // Both field and frame widgets share common elements

    getPrevOperationDOM: function () {
        return $("<select />")
            .attr("id", "prev-op")
            .css("display", "inline")
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
        } else if (action == "disable")
            ph.first().remove()
        else
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
                .addClass("row collapse")
                .append([
                    $("<div/>")
                        .addClass("large-1 small-1 columns multiseek-range-field-label")
                        .text(gettext("from")),

                    $("<div/>")
                        .addClass("large-5 small-5 columns")
                        .append([
                            $("<input type=text id=value_min size=4 />")]),

                    $("<div/>")
                        .addClass("large-1 small-1 columns multiseek-range-field-label")
                        .text(gettext("to")),

                    $("<div/>")
                        .addClass("large-5 small-5 columns")
                        .append([
                            $("<input type=text id=value_max size=4 />")])
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
                .addClass("row collapse")
                .append([
                    $("<div/>")
                        .addClass("small-11 columns")
                        .append(
                            $("<input data-type=search id='value' type='text' />")
                                .prop("data-id", null)
                                .autocomplete({
                                    minLength: 0,
                                    source: this.options.url,
                                    change: $.proxy(function (evt, ui) {
                                        if (ui.item == null) {
                                            alert(gettext("Please select value from the dropdown."));
                                            this.element.children().first().val('');
                                            this.element.children().first().focus();
                                        }

                                        $(evt.target).attr("data-id", null);
                                    }, this),
                                    select: function (evt, ui) {

                                        $(evt.target).prop("data-id", ui.item.id);
                                    }
                                })
                        ),
                    $("<div/>")
                        .addClass("small-1 columns")
                        .append(
                            $("<span/>")
                                .addClass("postfix")
                                .text("X")
                                .click($.proxy(function () {
                                    this.element.find("#value").first().val('').focus();
                                }, this))
                        )
                ])
        );

        this.element.find("#value").focus(function (evt) {
            $(evt.target).autocomplete("search");
        });
    },

    getValue: function () {
        return this.element.find("#value").first().prop("data-id");
    },

    setValue: function (value) {
        value = $.parseJSON(value);
        var elem = this.element.find("#value").first();
        elem.prop("data-id", value[0]);
        elem.val(value[1]);
    }
});


$.widget("multiseek.multiseekValueListValue", $.multiseek.multiseekBaseValue, {
    _create: function () {
        var element = $('<select/>')
            .attr("class", "values")
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
            .attr("size", "10");

        installDatePicker(element);

        this.element.append(
            $("<div/>")
                .attr("class", "row collapse")
                .append([
                    $("<div/>")
                        .attr("class", "large-5 small-5 columns")
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
                                .attr("size", "10");

                installDatePicker(element);
                row.append([
                    $("<div/>")
                        .attr("class", "large-2 small-2 columns")
                        .append($("<center/>").text("—")),
                    $("<div/>")
                        .attr("class", "large-5 small-5 columns")
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
        /* The first select -- the one with field type (first, last, address
         ... */
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
        // TODO: namespace? for vars like fields.
        fields.forEach(function (value) {
            select.append($('<option/>').val(value).html(value));
        });
        this.typeSelect().change();
    },


    opSelect: function () {
        /* The second select -- the one with field operations (equals, different,
         in range ... */
        return this.element.find("#op");
    },

    opSelectChanged: function (evt) {
        this.updateValueWidget();
    },

    updateOpsSelect: function () {
        /* Set operations values according to selected type. */
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
        /* The third THING -- something with an ID of 'value', usually an
         input field or a select or 2 input fields, or ... */
        return this.element.find("#value-placeholder").children().first();

    },

    initializeValueWidget: function () {
        /* initialize value widget, when the type is changed. */

        var p = this.element.find("#value-placeholder");
        try {
            p[this.getWidgetType()]("destroy"); // children().remove();
        } catch (Error) {

        };

        p.children().remove();
        var x = p.append("<span/>");
        p = $(p.children()[0]);

        switch (this.getFieldType()) {
            case 'autocomplete':
                p.multiseekAutocompleteValue(
                    {'url': autocompletes[this.getFieldName()]})
                break;

            default:
                p[this.getWidgetType()]({'fieldName': this.getFieldName()});
                break;

        }


    },

    updateValueWidget: function () {
        /* update value widget basing on 1st and 2nd select. Can be used for
         * range fields, from-to - if for some operations you want to add
         * additional field, like for date field. */


        this.valueElement()[this.getWidgetType()]('update',
            this.opSelect().val(),
            this.opSelect()[0].selectedIndex);


    },

    setType: function (type) {
        /* This sets the field type (first widget) AND fills the option
         list for the second widget. */
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
    // TODO: NAMESPACE THIS
    'type': 0,
    'operation': 0,
    'value': null
};

$.widget("multiseek.multiseekFrame", $.multiseek.multiseekBase, {

    makeFrameDOM: function (element) {
        // USES DOM
        element
            .attr("id", "frame-" + multiseek.frame_counter)
            .attr("class", "multiseekFrame")
            .append([

                $('<div/>')
                    .attr("id", "prev-op-placeholder"),

                $("<fieldset />")
                    .attr("class", "multiseek-fieldset")
                    .append([
                        $("<div/>")
                            .attr("id", "field-list"),
                        $("<button/>")
                            .attr("id", "add_field")
                            .addClass("small")
                            .text(gettext("Add field"))
                            .click($.proxy(function (evt) {
                                evt.preventDefault();
                                this.addFieldViaButton();
                            }, this)),
                        " ",
                        $("<button/>")
                            .attr("id", "add_frame")
                            .addClass("small")
                            .text(gettext("Add frame"))
                            .click($.proxy(function (evt) {
                                    evt.preventDefault();
                                    this.addFrameViaButton();
                                }, this
                            ))
                    ])
            ]);
    },

    _create: function () {
        this.makeFrameDOM(this.element);
        multiseek.frame_counter++;
    },


    fieldList: function () {
        // USES DOM
        return this.element.children("fieldset").children("#field-list");
    },

    noFields: function () {
        // USES DOM
        return this.fieldList().children().length;
    },

    empty: function () {
        return this.noFields() == 0;
    },

    removeFrame: function (id) {
        var for_removal = this.fieldList().find("#" + id);

        var next = for_removal.next();
        for_removal.remove()
        next.multiseekBase().multiseekBase("enableOrDisablePrevOp");

        if (this.empty() && this.element.attr("id") != "frame-0")
            this.removeSelf();
    },

    parentFrame: function () {
        // USES DOM
        // TODO: the worst way to find parent (markup-dependent). update to use some data arugmennt or sth
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
        fld.remove();
        next.multiseekBase().multiseekBase("enableOrDisablePrevOp");

        // remove frame if empty
        if (this.empty())
            this.removeSelf();
    },

    getFieldDOM: function (id) {
        // USES DOM
        return $("<field/>")
            .addClass("row collapse")
            .attr("id", id)
            .append([
                $("<div/>")
                    .addClass("large-1 small-2 columns")
                    .append(
                        $('<div/>').attr("id", "prev-op-placeholder")
                    ),

                $("<div/>")
                    .addClass("large-3 small-6 small columns")
                    .append(
                        $("<select/>")
                            .attr("id", "type")
                    ),
                $("<div/>")
                    .addClass("large-2 small-4 columns")
                    .append(
                        $("<select/>")
                            .attr("id", "op")),
                $("<div/>")
                    .addClass("large-5 small-10 columns")
                    .attr("id", "value-placeholder"),
                $("<div/>")
                    .addClass("large-1 small-2 columns")
                    .append(
                        $("<button/>")
                            .text("X")
                            .attr("id", "close-button")
                            .addClass('small radius ')
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

        elem = this.getFieldDOM(id);
        this.fieldList().append(elem);

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
        fr.multiseekFrame();
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

    serialize: function () {
        var ret = [];

        ret.push(this.getPrevOperationValue());

        this.fieldList().children().each($.proxy(function (no, elem) {
            if ($(elem).attr("id").startsWith("field")) {
                ret.push($(elem).multiseekField("serialize"));
                return;
            }
            ret.push($(elem).multiseekFrame("serialize"));
        }, this));

        return ret;
    }
});

function formOrdering() {
    ret = {};

    $(".multiseek-ordering").each(function (no, elem) {
        pn = "order_" + no;
        ret[pn] = $(elem).find(":selected").val();

        pn = pn + "_dir";
        if ($("input[name=" + pn + "]:checked").length)
            ret[pn] = "1";
    });
    return ret;
}

function formReportType() {
    sel = $("select[name=_ms_report_type]");
    if (sel.length) {
        return sel.val();
    }
}

function formAsJSON() {
    return JSON.stringify(
        {'form_data': $("#frame-0").multiseekFrame("serialize"),
            'ordering': formOrdering(),
            'report_type': formReportType()
        }); // <div id=#frame-0>
}

function submitEvent(button) {
    var value = formAsJSON();

    var form = $("<form/>").attr({
        method: "post",
        action: "./results/",
        target: "list_frame"
    }).append($("<input/>").attr('name', 'json').attr({"value": value}));

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
        'name': prompt(gettext("Form name?"))
    };

    if (dct.name == null)
        return;

    if (dct.name == '') {
        alert(gettext("Form name must not be empty."));
        return;
    }

    dct.public = confirm(
        gettext("Should the form be available for every user of this website?"));

    var url = multiseek.SAVE_FORM_URL;
    var error = gettext('There was a server-side error. The form was NOT saved.');
    var saved = gettext('Form was saved.');
    var form_exists = gettext('There is already a form with such name in the database. Overwrite?');

    $.post(url, dct,
        function (data, textStatus, jqXHR) {
            if (textStatus == 'success') {

                if (data.result == 'saved') {
                    alert(saved);
                    updateFormSelector(data.pk, dct['name']);
                } else if (data.result == 'overwrite-prompt') {
                    if (confirm(form_exists)) {
                        dct['overwrite'] = true;
                        $.post(url, dct,function (data, textStatus, jqXHR) {
                            if (textStatus == 'success') {
                                if (data.result == 'saved') {
                                    alert(saved);
                                    updateFormSelector(data.pk, dct['name']);
                                } else
                                    alert(data.result);
                            } else
                                alert(error);
                        }).error(function () {
                                alert(error);
                            });
                        ;
                    }
                } else
                    alert(data.result);

            } else
                alert(err);
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

window.multiseek.removeFromResults = function(id){
    var elem = $("#multiseek-row-" + id).children(".multiseek-element");
    var deco =  elem.css("text-decoration");

    var css_after = 'line-through';
    var url = '../remove-from-results/' + id

    if (deco.startsWith("line-through")) {
        css_after = 'none';
        url = '../remove-from-removed-results/' + id;
    }

    $.get(url, function(data){
        elem.css("text-decoration", css_after);
    });
}