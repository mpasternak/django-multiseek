/* Counters, that give us unique ID number for fields and frames */
var counter = 1;
var field_counter = 0;
var autocomplete_counter = 0;
var LOAD_FORM_URL = './load_form/';
var SAVE_FORM_URL = './save_form/';

function setFieldOperationAndTypeEvent(event) {
    /* Ustaw pole z operacjami (drugi select) ORAZ pole wyszukiwania (czyli TRZECIE pole)
     z poziomu EVENTU wysyłanego przez pole z polami (pierwszy select) */
    var select = event.currentTarget;
    if (select != undefined) {
        setFieldOperationAndTypeField(select);
    }
}

function fieldOperationChangedEvent(event) {
    /* Field's operation has been changed. */
    var select = event.currentTarget;
    if (select != undefined) {
        fieldOperationChanged($(select).parent());
    }
}

function getFieldType(field) {
    return types[field.children().first().val()];
}

function getFieldOp(field) {
    return field.children().next().first()[0].selectedIndex;
}

function getFieldWidget(field) {
    return $(field.children().next().next()[0]);
}
function fieldOperationChanged(field) {
    field_type = getFieldType(field);
    switch (field_type) {
        case "date":
            op = getFieldOp(field);
            w = getFieldWidget(field);
            if (op > 5) {
                // range
                console.log('range');
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
                console.log('single');
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
}

function setFieldOperationAndTypeField(select) {
    /* Ustaw pole z operacjami (drugi select) ORAZ pole wyszukiwania (czyli TRZECIE pole) */
    var select = $(select);

    var pole = select.val();

    var ops_select = select.next();
    ops_select.children().remove();
    ops[pole].forEach(function (value) {
        ops_select.append($('<option/>').val(value).html(value));
    });

    var type_field = ops_select.next();

    var typ = types[pole];
    var element;

    switch (typ) {
        case "date":
            element = $('<input type="text" name="value" placeholder="' +
                gettext('today') + '" size="10" />');
            element.datepicker($.datepicker.regional[djangoLanguageCode]);
            element = $('<div style="display: inline;"/>').append(element);
            break;

        case "range":
            element = $(
                '<span class="range values" style="display: inline-block;">' +
                    '<input type="text" name="value_min" size="4" />-' +
                    '<input type="text" name="value_max" size="4" />' +
                    '</span>');
            break;

        case "value-list":
            element = $('<select class="values" name="value_list" />');
            value_lists[pole].forEach(function (v) {
                element.append($('<option/>').val(v).html(v));
            });
            break;

        case "autocomplete":
            element = $("#autocomplete-__no__").parent().clone();
            element.attr("data-autocomplete-url", autocompletes[pole]);

            element.children().each(function (numer, node) {
                updateNodeAttributes($(node), autocomplete_counter);
            });

            autocomplete_counter++;
            break;

        default:
        case "string":
            element = $('<input class="string values" type="text" name="value" />').attr('size', '30');
            break;
    }

    element.insertBefore(type_field);
    type_field.remove();

}

function fillFieldValues(field, values) {
    /* przyjmuje parametr - cały widget z polem, następnie wypełnia
     jego pierwszy select wartościami z tabeli fields, następnie
     jeszcze dodaje mu wydarzenie co-w-razie-zmiany pola.

     Funkcja używana do INICJALIZACJI świeżo dodanego clone'a
     do fieldsetu */

    var select = selectWithFields(field);
    select.children().remove();
    values.forEach(function (value) {
        select.append($('<option/>').val(value).html(value));
    });
    select.change(setFieldOperationAndTypeEvent);

    var second_select = selectWithOperations(field);
    second_select.change(fieldOperationChangedEvent);
}

function setFieldOperationAndValue(field, operation, value) {
    var type = types[selectWithFields(field).val()];

    var field_op = field.children()[1];
    $(field_op).val(operation);

    var widget = $(field.children()[2]);

    switch (type) {
        case "range":
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


}

function initializeField(field, type, operation, value) {
    /* Zainicjalizuj nowo dodany klon do fieldsetu */
    fillFieldValues(field, fields);
    selectWithFields(field).val(type);
    setFieldOperationAndTypeField(selectWithFields(field));
    setFieldOperationAndValue(field, operation, value);
}

function updateNodeAttributes(node, param) {
    /* Zmień wszystkie __no__ na numer pola
     */

    ['id', 'name', 'onclick'].forEach(function (name) {
        v = node.attr(name);

        if (v != '' && v != undefined)
            node.attr(name, node.attr(name).replace("__no__", param));
    });
}

function getFieldDict(field) {
    first_select = selectWithFields($(field));
    second_select = first_select.next();
    third_something = second_select.next();
    next_operation = third_something.next()

    return {'first_select': first_select,
        'second_select': second_select,
        'third_something': third_something,
        'next_operation': next_operation}
}

function getFieldValue(field) {
    field_dict = getFieldDict(field);

    field_type = field_dict.first_select.val();
    field_op = field_dict.second_select.val();

    ret = {
        'field': field_type,
        'operation': field_op
    }

    switch (types[field_type]) {
        case "date":
            op_idx = field_dict.second_select[0].selectedIndex;
            console.log(op_idx);
            if (op_idx > 5) {
                min = third_something.children().first().val();
                max = third_something.children().first().next().val();
                ret.value = [min, max];
            } else {
                ret.value = third_something.children().first().val();
            }
            break;

        case "range":
            min = third_something.children().first().val();
            max = third_something.children().first().next().val();
            ret.value = [min, max];
            break;

        case "autocomplete":
            ret.value = third_something.yourlabsWidget().select.val()
            break;

        case "string":
        default:
            ret.value = third_something.val();
            break;
    }

    return ret;
}

function getNextOperation(field) {
    var fieldDict = getFieldDict(field);

    if (fieldDict.next_operation.css("visibility") == "visible")
        return fieldDict.next_operation.val();

    return null;
}

/* ------------------------------------------------------------------------------------------- */
/* Wysyłka formularza na serwer */
/* ------------------------------------------------------------------------------------------- */


function serialize(topNode, level) {
    /*
     REKURSYWNA funkcja, tworząca obiekt JSON, który potem może być
     wykorzystany do wysłania na serwer i zapytania bazy danych.

     Struktura JSONa wygląda tak:
     [

     {'field': 'Tytuł oryginalny',
     'operator': 'równa się',
     'value': 'Wartość'},

     'AND',

     {'field': Zakres lat',
     'operator': 'nie zawiera',
     'value': ['1999', '2000']},

     'OR',

     [ { ... }, 'AND', { ... }, ]

     ]

     */

    var subframe = topNode.children().first();
    var fieldset = subframe.children().first();

    var cnt = 0;
    var ret = [];

    fieldset.children().each(function (no, elem) {

        if ($(elem).attr('id').indexOf('field') == 0) {

            field_value = getFieldValue(elem);
            next_operation = getNextOperation(elem);

            ret = ret.concat(field_value);

            if (next_operation)
                ret = ret.concat(next_operation);

        } else {
            ret = ret.concat([serialize($(elem), level + 1), ]);

            next_operation = $(elem).children().last().prev();
            if (next_operation.css("visibility") == "visible")
                ret = ret.concat(next_operation.val());
        }
    });

    return ret;
}

function formAsList() {
    return serialize($("#frame-0"), 0);
}

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
        {'form_data': formAsList(),
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

/* ------------------------------------------------------------------------------------------- */
/* Funkcje zwracające poszczególne elementy pola - współpracują na poziomie DOMu */
/* ------------------------------------------------------------------------------------------- */

function selectWithFields(field) {
    /* select tag, containing the fields - which is, the first select,
     containing field like: first name, last name, operation, title... */
    return field.children().first();
}

function selectWithOperations(field) {
    /* returns a select tag containing the list of operations available
     for a given field, which is: equal, not equal, different, exact... */
    return selectWithFields(field).next();
}

function get_join(pole) {
    /* SELECT z wartością LUB i I, czyli łącznik */
    return pole.children().last().prev();
}

function schowaj_lacznik(pole) {
    get_join(pole).attr('style', 'visibility: hidden;');
}

function set_join(pole, wartosc) {
    get_join(pole).val(wartosc)
}

function pokaz_lacznik(pole) {
    get_join(pole).attr('style', 'visibility: visible;');
}

function ostatnie_pole(frame) {
    /* Ostatnie "poziome" pole (czyli zestaw SELECT+SELECT+text+łącznik+przycisk X
     * w danej ramce */
    return frame.children(".subframe").children("#fieldset").children().last();
}

/* ------------------------------------------------------------------------------------------- */
/* Funkcje manipulujące polami i ramkami -- dodawanie, usuwanie  */
/* ------------------------------------------------------------------------------------------- */

function addField(root, type, operation, value) {

    var field = $('#field-__no__');
    var clone = field.clone();
    clone.attr('style', 'display: block;');

    /* pokaż łącznik czyli operację I/LUB poprzedniego elementu */
    pokaz_lacznik(ostatnie_pole(root));

    updateNodeAttributes(clone, field_counter++);

    root.children(".subframe").children('#fieldset').append(clone);

    /* schowaj łącznik czyli operację I/LUB dodawanego elementu, bo za nim nic nie ma */
    schowaj_lacznik(ostatnie_pole(root));

    initializeField(clone, type, operation, value);
}

function addFieldViaButton(button) {
    addField($(button).parent().parent());
}

function removeField(button) {
    var field = $(button).parent();

    /* ostatni element w RAMCE */
    if (field.parent().children().length == 1) {

        /* Jeżeli to ostatnia ramka, to się zbuntuj: */
        if (field.parent().parent().parent().attr('id') == 'frame-0') {
            alert(last_field_remove_message);
            return;
        }

        /* Jeżeli nie -- usuń pustą ramkę: */

        /* ... ale wcześniej schowaj łącznik poprzedniego pola: */
        var poprzednie_pole = field.parent().parent().parent().prev();
        schowaj_lacznik(poprzednie_pole);

        /* ... i spokojnie usuń pustą ramkę */
        field.parent().parent().parent().remove();


        return;
    }

    if (field.parent().children().last().attr('id') == field.attr('id')) {
        /* ostatni element w wierszu */
        var poprzednie_pole = field.parent().children().last().prev();
        schowaj_lacznik(poprzednie_pole);
    }

    field.remove();
}

function addFrame(root) {
    var base = $('#frame-__no__');
    var clone = base.clone();
    clone.attr('style', 'display: block;');
    updateNodeAttributes(clone, counter++);

    var ost_pol = ostatnie_pole(root);
    pokaz_lacznik(ost_pol);

    root.children(".subframe").children('#fieldset').append(clone);

    // addField(clone);
}

function addFrameViaButton(node) {
    addFrame($(node).parent().parent());
    // Tryb interaktywny -- dodaj jeszcze pole
    addField($("#frame-" + (counter - 1)), fields[0], ops[fields[0]][0], "");
}

