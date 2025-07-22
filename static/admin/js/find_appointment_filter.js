(function () {
    'use strict';

    // Wait for jQuery to be available
    function waitForJQuery(callback) {
        if (typeof django !== 'undefined' && django.jQuery) {
            callback(django.jQuery);
        } else if (typeof $ !== 'undefined') {
            callback($);
        } else {
            setTimeout(function () {
                waitForJQuery(callback);
            }, 100);
        }
    }

    waitForJQuery(function ($) {
        $(document).ready(function () {
            var doctorSelect = $('#id_doctor');
            var tipoTurnoSelect = $('#id_tipo_de_turno');

            if (doctorSelect.length === 0 || tipoTurnoSelect.length === 0) {
                return; // Exit if elements don't exist
            }

            // Function to update tipo_de_turno options based on selected doctor
            function updateTipoTurnoOptions() {
                var selectedDoctorId = doctorSelect.val();

                if (!selectedDoctorId) {
                    // Clear options if no doctor is selected
                    tipoTurnoSelect.empty();
                    tipoTurnoSelect.append('<option value="">---------</option>');
                    return;
                }

                // Show loading state
                tipoTurnoSelect.prop('disabled', true);

                // Make AJAX request to get filtered tipo_de_turno options
                $.ajax({
                    url: '/admin/sanatorio_allende/findappointment/get-tipos-turno/' + selectedDoctorId + '/',
                    method: 'GET',
                    success: function (data) {
                        // Clear existing options
                        tipoTurnoSelect.empty();
                        tipoTurnoSelect.append('<option value="">---------</option>');

                        // Add new options based on the response
                        if (data.tipos_turno && data.tipos_turno.length > 0) {
                            $.each(data.tipos_turno, function (index, tipo) {
                                tipoTurnoSelect.append(
                                    $('<option></option>')
                                        .attr('value', tipo.id)
                                        .text(tipo.name)
                                );
                            });
                        }

                        // Re-enable the select
                        tipoTurnoSelect.prop('disabled', false);
                    },
                    error: function () {
                        // Handle error - re-enable select and show error message
                        tipoTurnoSelect.prop('disabled', false);
                        console.error('Error fetching tipo_de_turno options');
                    }
                });
            }

            // Bind the change event to the doctor select after a delay to avoid Django admin triggers
            // $('.related-widget-wrapper select').trigger('change');
            setTimeout(function () {
                doctorSelect.on('change', updateTipoTurnoOptions);
            }, 500);

            // If there's already a doctor selected on page load, update the options
            // Commented out to prevent triggering on page load
            //if (doctorSelect.val()) {
            //    updateTipoTurnoOptions();
            //}
        });
    });

})(); 