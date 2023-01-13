Overview of ownership and usage between components

```mermaid
graph
    application --> window
    window --> package_view
    window --> flatpak_view
    window --> queue_view
    window --> progress
    window --> presenter
    window --> package_info
    window --> package_settings
    window --> preferences
    package_view --o presenter
    package_view --> transaction_result
    queue_view --o presenter
    presenter --> dnf_backend
    presenter --> package_cache
    package_cache --o dnf_backend
    flatpak_view --> flatpak_installer
    flatpak_view --> flatpak_confirmation
    flatpak_view --> flatpak_backend
    dnf_backend --o progress
    flatpak_transaction --o progress
    flatpak_backend --> flatpak_transaction
```

