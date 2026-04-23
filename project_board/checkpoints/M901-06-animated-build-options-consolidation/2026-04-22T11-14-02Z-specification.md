### [M901-06-animated-build-options-consolidation] SPECIFICATION — legacy module deletion scope
**Would have asked:** Should deletion of the "original 7 files" include a compatibility shim at `animated_build_options.py`, or must all legacy filenames disappear entirely?
**Assumption made:** Keep strict acceptance interpretation: all seven legacy `animated_build_options*.py` files are deleted, and compatibility is preserved through the new `utils.build_options` package API and updated imports only.
**Confidence:** Medium

### [M901-06-animated-build-options-consolidation] SPECIFICATION — spider-eye behavior ownership note
**Would have asked:** The notes mention moving spider-eye-specific logic to a spider builder; is that migration in scope for this ticket or deferred?
**Assumption made:** Treat spider-eye relocation as non-blocking advisory context; this ticket preserves existing runtime behavior and only consolidates animated build options into `schema.py` and `validate.py` without moving behavior to builders.
**Confidence:** High
