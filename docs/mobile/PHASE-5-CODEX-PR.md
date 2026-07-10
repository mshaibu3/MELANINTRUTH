# Phase 5 Codex Review Checklist

Review the Phase 5 pull request against these invariants:

* no beauty, whitening, lightening, smoothing, reshaping, or identity-changing behavior;
* no raw-image, password, access-token, refresh-token, or signed-URL logging;
* access tokens remain memory-only;
* refresh-session material uses platform secure storage and is cleared after invalid refresh or deletion;
* restored sessions require server-side consent revalidation;
* captures fail closed on cancellation, denial, empty bytes, unsupported type, oversize files, or non-HTTPS signed URLs;
* SHA-256, content type, and byte size are sent consistently in upload request and completion calls;
* only the idempotent binary PUT is automatically retried;
* API state-creating calls are not silently replayed;
* all existing backend, API integration, and mobile workflows remain green.
