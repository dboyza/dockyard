The runtime stage has exactly the application files it needs and a process identity with less authority.
This is useful defense in depth, not proof that the whole application is secure.
Explain which build-time files were excluded and what would happen if their ownership prevented the non-root process from reading VERSION.
