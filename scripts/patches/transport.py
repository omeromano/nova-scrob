def apply(ctx):
    for rel in (
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConfig.java",
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobCredentials.java",
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionState.java",
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionCheck.java",
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnection.java",
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobAuthManager.java",
        "MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java",
    ):
        ctx.install_template(rel)
