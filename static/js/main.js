document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // COMPANION FORM
    // =====================================================

    const solo = document.querySelector(
        'input[name="attendance_type"][value="solo"]'
    );

    const companion = document.querySelector(
        'input[name="attendance_type"][value="companion"]'
    );

    const companionForm = document.querySelector(
        ".companion-form"
    );


    const requiredCompanionFields = [
        "companion_first_name",
        "companion_last_name",
        "companion_phone"
    ];


    function syncCompanion() {

        if (
            !solo ||
            !companion ||
            !companionForm
        ) {
            return;
        }


        const companionInputs =
            companionForm.querySelectorAll(
                "input"
            );


        // =============================================
        // WITH COMPANION
        // =============================================

        if (companion.checked) {

            companionForm.classList.add(
                "is-visible"
            );


            companionInputs.forEach(
                (input) => {

                    input.disabled = false;

                }
            );


            requiredCompanionFields.forEach(
                (name) => {

                    const input =
                        companionForm.querySelector(
                            `[name="${name}"]`
                        );


                    if (input) {

                        input.required = true;

                    }

                }
            );

        }

        // =============================================
        // SOLO
        // =============================================

        else {

            companionForm.classList.remove(
                "is-visible"
            );


            companionInputs.forEach(
                (input) => {

                    input.disabled = true;

                    input.required = false;

                    input.value = "";

                }
            );

        }

    }


    // =====================================================
    // RADIO EVENTS
    // =====================================================

    solo?.addEventListener(
        "change",
        syncCompanion
    );


    companion?.addEventListener(
        "change",
        syncCompanion
    );


    // Run when page loads
    syncCompanion();



    // =====================================================
    // SMOOTH SCROLL
    // =====================================================

    document
        .querySelectorAll(
            'a[href^="#"]'
        )
        .forEach(
            (link) => {

                link.addEventListener(
                    "click",
                    (event) => {

                        const id =
                            link.getAttribute(
                                "href"
                            );


                        if (
                            !id ||
                            id === "#"
                        ) {
                            return;
                        }


                        const target =
                            document.querySelector(
                                id
                            );


                        if (!target) {
                            return;
                        }


                        event.preventDefault();


                        target.scrollIntoView({
                            behavior: "smooth",
                            block: "start"
                        });

                    }
                );

            }
        );

});