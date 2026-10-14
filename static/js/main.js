/**
 * Student Attendance Tracker - Vanilla JavaScript Interactions
 * Handles:
 * - Mobile sidebar toggle
 * - Dismissible flash message toasts
 * - Native accessible confirmation dialog (<dialog>)
 * - Attendance bulk marking (Present, Absent, Leave)
 * - Bulk import checkbox selection
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // Mobile Sidebar Drawer Toggle
    // -------------------------------------------------------------
    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    const mobileSidebar = document.getElementById("mobile-sidebar");
    const mobileBackdrop = document.getElementById("mobile-backdrop");
    const closeSidebarBtn = document.getElementById("close-sidebar-btn");

    function openMobileSidebar() {
        if (mobileSidebar && mobileBackdrop) {
            mobileSidebar.classList.remove("-translate-x-full");
            mobileBackdrop.classList.remove("hidden");
            document.body.classList.add("overflow-hidden");
        }
    }

    function closeMobileSidebar() {
        if (mobileSidebar && mobileBackdrop) {
            mobileSidebar.classList.add("-translate-x-full");
            mobileBackdrop.classList.add("hidden");
            document.body.classList.remove("overflow-hidden");
        }
    }

    if (mobileMenuBtn) mobileMenuBtn.addEventListener("click", openMobileSidebar);
    if (closeSidebarBtn) closeSidebarBtn.addEventListener("click", closeMobileSidebar);
    if (mobileBackdrop) mobileBackdrop.addEventListener("click", closeMobileSidebar);

    // -------------------------------------------------------------
    // Flash Message Toast Auto-dismiss
    // -------------------------------------------------------------
    const toasts = document.querySelectorAll(".toast-item");
    toasts.forEach((toast) => {
        // Auto-fade after 5 seconds if not an error
        const isError = toast.getAttribute("data-type") === "error";
        if (!isError) {
            setTimeout(() => {
                toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
                toast.style.opacity = "0";
                toast.style.transform = "translateY(-8px)";
                setTimeout(() => toast.remove(), 400);
            }, 6000);
        }

        const dismissBtn = toast.querySelector(".toast-dismiss-btn");
        if (dismissBtn) {
            dismissBtn.addEventListener("click", () => {
                toast.remove();
            });
        }
    });

    // -------------------------------------------------------------
    // Universal Accessible Confirmation Dialog (<dialog>)
    // -------------------------------------------------------------
    const confirmModal = document.getElementById("confirm-dialog");
    const modalTitle = document.getElementById("modal-title");
    const modalMessage = document.getElementById("modal-message");
    const modalConfirmBtn = document.getElementById("modal-confirm-btn");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    let currentPendingAction = null;

    window.openConfirmModal = function (title, message, confirmText, confirmClass, onConfirm) {
        if (!confirmModal) {
            if (confirm(message)) onConfirm();
            return;
        }

        modalTitle.textContent = title || "Confirm Action";
        modalMessage.textContent = message || "Are you sure you want to proceed?";
        modalConfirmBtn.textContent = confirmText || "Confirm";

        // Reset classes
        modalConfirmBtn.className = "px-4 py-2 text-sm font-medium rounded-lg text-white transition shadow-sm " + (confirmClass || "bg-indigo-600 hover:bg-indigo-700");

        currentPendingAction = onConfirm;
        confirmModal.showModal();
    };

    if (modalConfirmBtn) {
        modalConfirmBtn.addEventListener("click", () => {
            confirmModal.close();
            if (typeof currentPendingAction === "function") {
                currentPendingAction();
                currentPendingAction = null;
            }
        });
    }

    if (modalCancelBtn) {
        modalCancelBtn.addEventListener("click", () => {
            confirmModal.close();
            currentPendingAction = null;
        });
    }

    // Close dialog on backdrop click
    if (confirmModal) {
        confirmModal.addEventListener("click", (e) => {
            const rect = confirmModal.getBoundingClientRect();
            const isInDialog =
                rect.top <= e.clientY &&
                e.clientY <= rect.top + rect.height &&
                rect.left <= e.clientX &&
                e.clientX <= rect.left + rect.width;
            if (!isInDialog) {
                confirmModal.close();
                currentPendingAction = null;
            }
        });
    }

    // -------------------------------------------------------------
    // Generic Delete Confirmation Hook
    // -------------------------------------------------------------
    document.querySelectorAll(".confirm-delete-form").forEach((form) => {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const itemName = form.getAttribute("data-item-name") || "this record";
            window.openConfirmModal(
                "Delete Student Record",
                `Are you sure you want to permanently delete "${itemName}"? All associated attendance records will also be removed.`,
                "Delete Student",
                "bg-rose-600 hover:bg-rose-700 focus:ring-rose-500",
                () => form.submit()
            );
        });
    });

    // -------------------------------------------------------------
    // Attendance Sheet Bulk Marking
    // -------------------------------------------------------------
    window.markAllAttendance = function (status) {
        const radios = document.querySelectorAll(`input[type="radio"][value="${status}"]`);
        radios.forEach((r) => {
            r.checked = true;
            // Trigger visual highlight update
            const parent = r.closest(".attendance-pill-group");
            if (parent) {
                parent.querySelectorAll(".attendance-pill").forEach((pill) => pill.classList.remove("ring-2", "ring-offset-1"));
                const currentLabel = r.closest("label");
                if (currentLabel) currentLabel.classList.add("ring-2", "ring-offset-1");
            }
        });
    };

    // -------------------------------------------------------------
    // Bulk Import Checkbox Helpers
    // -------------------------------------------------------------
    const selectAllCheckbox = document.getElementById("select-all-import-rows");
    const rowCheckboxes = document.querySelectorAll(".import-row-checkbox");

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", (e) => {
            const isChecked = e.target.checked;
            rowCheckboxes.forEach((cb) => {
                cb.checked = isChecked;
            });
            updateSelectedCount();
        });
    }

    rowCheckboxes.forEach((cb) => {
        cb.addEventListener("change", () => {
            updateSelectedCount();
        });
    });

    window.selectOnlyValidImportRows = function () {
        rowCheckboxes.forEach((cb) => {
            const status = cb.getAttribute("data-status");
            cb.checked = status === "VALID";
        });
        if (selectAllCheckbox) selectAllCheckbox.checked = false;
        updateSelectedCount();
    };

    function updateSelectedCount() {
        const selectedCount = document.querySelectorAll(".import-row-checkbox:checked").length;
        const countBadge = document.getElementById("selected-import-count");
        if (countBadge) {
            countBadge.textContent = selectedCount;
        }
    }
});
