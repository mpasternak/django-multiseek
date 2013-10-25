/* Counters, that give us unique ID number for fields and frames */
var counter = 0;
var field_counter = 0;
var autocomplete_counter = 0;
var LOAD_FORM_URL = './load_form/';
var SAVE_FORM_URL = './save_form/';

$.widget("multiseek.multiseekBase", {
    // Both field and frame widgets share common elements

    prevOperation: function () {
        return this.element.children("#prev-op");
    },

    getPrevOperationValue: function () {
        var prev_op = this.prevOperation();
        if (prev_op.is(":visible"))
            return prev_op.val();
        return null;
    },

    tunePrevOpVisibility: function () {
        if (this.element.prev().length) {
            this.prevOperation().show();
            return;
        }
        this.prevOperation().hide();
    }


});

$.widget("multiseek.multiseekField", $.multiseek.multiseekBase, {

    _create: function () {
        this.typeSelect().change($.proxy(this.typeSelectChanged, this));
        this.opSelect().change($.proxy(this.opSelectChanged, this));

        this.setTypeSelectValues();
        this.tunePrevOpVisibility();
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


    valueWidget: function () {
        /* The third THING -- something with an ID of 'value', usually an
         input field or a select or 2 input fields, or ... */
        return this.element.find("#value");
    },

    initializeValueWidget: function () {
        /* initialize value widget, when the type is changed. */

        var element;

        switch (this.getFieldType()) {
            case "date":
                element = $('<input type="text" name="value" placeholder="' +
                    gettext('today') + '" size="10" />');
                element.datepicker($.datepicker.regional[djangoLanguageCode]);
                element = $('<div style="display: inline;" id="value" />').append(element);
                break;

            case "range":
                element = $(
                    '<span class="range values" id="value" style="display: inline-block;">' +
                        '<input type="text" name="value_min" size="4" />-' +
                        '<input type="text" name="value_max" size="4" />' +
                        '</span>');
                break;

            case "value-list":
                element = $('<select class="values" name="value_list" />');
                value_lists[this.getFieldName()].forEach(function (v) {
                    element.append($('<option/>').val(v).html(v));
                });
                break;

            case "autocomplete":
                var id = "autocomplete-" + autocomplete_counter;

                element = $("<span/>")
                    .css("display", "inline-block")
                    .css("clear", "both")
                    .attr("class", "autocomplete-light-widget")
                    .attr("data-bootstrap", "normal")
                    .attr("data-autocomplete-choice-selector", "[data-value]")
                    .attr("data-max-values", "1")
                    .attr("data-minimum-characters", "0")
                    .attr("data-autocomplete-placeholder", gettext("type to lookup..."))
                    .attr("data-autocomplete-url", autocompletes[this.getFieldName()])
                    .append([
                        $("<input/>")
                            .attr("type", "text")
                            .attr("id", "id"),
                        $("<span class=deck/>"),
                        $("<select/ >")
                            .css("display", "none")
                            .attr("class", "value-select")
                            .attr("id", "value")
                            .attr("name", id + "-value"),
                        $("<span/>")
                            .css("display", "none")
                            .attr("class", "remove")
                            .text(gettext("Remove this choice")),
                        $("<span/>")
                            .css("display", "none")
                            .attr("class", "choice-template").append([
                                $("<span/>")
                                    .attr("class", "choice")
                            ])
                    ])
                autocomplete_counter++;
                break;

            default:
            case "string":
                element = $('<input class="string values" type="text" name="value" />').attr('size', '30');
                break;
        }

        current = this.element.find("#value");
        element = element.attr("id", "value");
        element.insertBefore(current);
        current.remove();
    },

    updateValueWidget: function () {
        /* update value widget basing on 1st and 2nd select. Can be used for
         * range fields, from-to - if for some operations you want to add
         * additional field, like for date field. */

        switch (this.getFieldType()) {
            case "date":
                op = this.opSelect()[0].selectedIndex;
                w = this.valueWidget();
                if (op > 5) {
                    // range
                    if (w.children().length == 1) {
                        // add extra field
                        w.append("-");
                        element = $('<input type="text" name="value" placeholder="' +
                            gettext('today') + '" size="10" />');
                        element.datepicker($.datepicker.regional[djangoLanguageCode]);
                        w.append(element);
                    }
                } else {
                    // single field
                    if (w.children().length > 1) {
                        // remove extra field
                        w.contents()[1].remove();
                        w.contents()[1].remove();
                    }
                }
                return;

            default:
                return;
        }
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
        var widget = this.valueWidget();

        switch (this.getFieldType()) {
            case "date":
                value = $.parseJSON(value);
                $(widget.children()[0]).val(value[0]);
                op_idx = this.opSelect()[0].selectedIndex;
                if (op_idx > 5)
                    $(widget.children()[1]).val(value[1]);
                break;


            case "range":
                value = $.parseJSON(value);
                $(widget.children()[0]).val(value[0]);
                $(widget.children()[1]).val(value[1]);
                break;

            case "autocomplete":
                var widget = widget.yourlabsWidget();
                widget.selectChoice($("<div data-value=" + value[0] + "" +
                    ">" + value[1] + "</div>"))
                break;

            case "string":
            case "value-list":
            default:
                widget.val(value);
                break;
        }
    },

    getValue: function () {
        var third_something = this.valueWidget();

        switch (this.getFieldType()) {
            case "date":
                min = third_something.children().first().val();
                op_idx = this.opSelect()[0].selectedIndex;
                if (op_idx > 5) {
                    max = third_something.children().first().next().val();
                    return JSON.stringify([min, max]);
                }
                return JSON.stringify([min,]);

            case "range":
                min = third_something.children().first().val();
                max = third_something.children().first().next().val();
                return JSON.stringify([parseInt(min), parseInt(max)]);

            case "autocomplete":
                return third_something.yourlabsWidget().select.val();

            case "string":
            default:
                return third_something.val();
        }

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

$.fn.multiseekPrevField = function () {

    return $("<select />")
        .attr("id", "prev-op")
        .css("display", "inline")
        .append([
            $("<option/>").html(gettext("and")).attr("value", "and"),
            $("<option/>").html(gettext("or")).attr("value", "or")
        ]).hide()
}

$.widget("multiseek.multiseekFrame", $.multiseek.multiseekBase, {

    _create: function () {

        this.element
            .attr("id", "frame-" + counter)
            .attr("class", "multiseekFrame")
            .append([

                $.fn.multiseekPrevField(),

                $("<fieldset/>")
                    .append([
                        $("<div/>")
                            .attr("id", "field-list"),
                        $("<button/>")
                            .attr("id", "add_field")
                            .text(gettext("Add field"))
                            .click($.proxy(this.addField, this)),

                        $("<button/>")
                            .attr("id", "add_frame")
                            .text(gettext("Add frame"))
                            .click($.proxy(this.addFrameViaButton, this))
                    ])
            ]);

        // TODO: namespace THIS
        counter++;
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
        for_removal.remove()
        next.multiseekBase().multiseekBase("tunePrevOpVisibility");

        if (this.empty() && this.element.attr("id") != "frame-0")
            this.removeSelf();
    },

    parentFrame: function () {
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
        next.multiseekBase().multiseekBase("tunePrevOpVisibility");

        // remove frame if empty
        if (this.empty())
            this.removeSelf();
    },


    addField: function (type, operation, value, op) {
        // TODO: namespace field_counter
        var id = "field-" + field_counter;
        var has_elements = this.fieldList().children().length;

        this.fieldList().append(
            $("<field/>")
                .attr("id", id)
                .attr("class", "field")
                .append([
                    $.fn.multiseekPrevField(),

                    $("<select/>")
                        .attr("id", "type"),
                    $("<select/>")
                        .attr("id", "op"),
                    $("<div/>")
                        .attr("id", "value"),
                    $("<button/>")
                        .text("X")
                        .attr("id", "close-button")
                        .data("for-field", id)
                        .click($.proxy(this.removeField, this))
                ]));

        var fld = $("#" + id);
        fld.multiseekField();
        if (type && operation)
            fld.multiseekField("setValue", type, operation, value, op);
        field_counter++;

        if (has_elements)
            fld.multiseekField("prevOperation").show();
    },

    addFrame: function (prevOpValue) {
        var id = "frame-" + counter;
        var has_elements = this.fieldList().children().length;
        this.fieldList().append(
            $("<div/>")
                .attr("id", id)
        );
        var fr = $("#" + id);
        fr.multiseekFrame();
        counter++;
        if (has_elements)
            fr.multiseekFrame("prevOperation").show();
        if (prevOpValue)
            fr.multiseekFrame("prevOperation").val(prevOpValue);

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

    var url = SAVE_FORM_URL;
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
    ).error(function () {
            alert(error);
        });
}

function loadForm(select) {
    if (confirm(gettext("Are you sure you want to load selected form?")))
        location.href = LOAD_FORM_URL + $(select).val();
    $(select).val('');
}
