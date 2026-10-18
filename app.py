import streamlit as st
from pathlib import Path

# All files live in this folder, so the app can never touch its own code
BASE_DIR = Path("my_files")
BASE_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="File Manager", page_icon="📁")


# ---------- helpers ----------
def get_path(name):
    """Return a safe path inside BASE_DIR, or None if the name is invalid."""
    name = Path(name.strip()).name  # drops any folder parts like ../
    if name in ("", ".", ".."):
        return None
    return BASE_DIR / name


def list_files():
    return sorted(p.name for p in BASE_DIR.iterdir() if p.is_file())


def flash(kind, message):
    """Save a message to show after the next rerun (kind: success/error/info/warning)."""
    st.session_state["flash"] = (kind, message)


def show_flash():
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        getattr(st, kind)(message)


# ---------- page header ----------
st.title("📁 File Manager")
st.caption(f"Working folder: `{BASE_DIR.resolve()}`")
show_flash()

files = list_files()

with st.sidebar:
    st.header("Your files")
    if files:
        for f in files:
            st.write(f"📄 {f}")
    else:
        st.write("No files yet.")

tab_create, tab_read, tab_update, tab_delete = st.tabs(
    ["➕ Create", "📖 Read", "✏️ Update", "🗑️ Delete"]
)

# ---------- CREATE ----------
with tab_create:
    # Changing this counter gives the form fresh (empty) widgets after a success
    st.session_state.setdefault("create_n", 0)
    n = st.session_state["create_n"]

    with st.form("create_form"):
        name = st.text_input("File name", placeholder="notes.txt", key=f"create_name_{n}")
        content = st.text_area("What do you want to write in this file?", height=200, key=f"create_content_{n}")
        submitted = st.form_submit_button("Create file")

    if submitted:
        path = get_path(name)
        if path is None:
            st.error("Please enter a valid file name.")
        elif path.exists():
            st.error("This file already exists!")
        else:
            try:
                path.write_text(content, encoding="utf-8")
            except Exception as err:
                st.error(f"An unexpected error occurred: {err}")
            else:
                flash("success", f"'{path.name}' created successfully.")
                st.session_state["create_n"] += 1
                st.rerun()

# ---------- READ ----------
with tab_read:
    if not files:
        st.info("No files to read yet. Create one first!")
    else:
        selected = st.selectbox("Choose a file", files, key="read_select")
        path = BASE_DIR / selected
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            st.error("This file isn't a plain-text file, so it can't be shown.")
        except Exception as err:
            st.error(f"An unexpected error occurred: {err}")
        else:
            st.text_area("The content in your file is:", value=text, height=300, disabled=True)
            st.caption(f"{path.stat().st_size} bytes")
            st.download_button("⬇️ Download", data=text, file_name=selected)

# ---------- UPDATE ----------
with tab_update:
    if not files:
        st.info("No files to update yet. Create one first!")
    else:
        selected = st.selectbox("Choose a file", files, key="update_select")
        path = BASE_DIR / selected
        action = st.radio("What do you want to do?", ["Rename", "Append", "Overwrite"], horizontal=True)

        if action == "Rename":
            with st.form("rename_form"):
                new_name = st.text_input("Enter the new name of the file", value=selected)
                go = st.form_submit_button("Rename")
            if go:
                new_path = get_path(new_name)
                if new_path is None:
                    st.error("Please enter a valid file name.")
                elif new_path.exists():
                    st.error("File already exists! Try a different name.")
                else:
                    try:
                        path.rename(new_path)
                    except Exception as err:
                        st.error(f"An error occurred: {err}")
                    else:
                        flash("success", f"Renamed '{selected}' to '{new_path.name}'.")
                        st.rerun()

        elif action == "Append":
            with st.form("append_form", clear_on_submit=True):
                data = st.text_area("What do you want to append?", height=150)
                go = st.form_submit_button("Append")
            if go:
                try:
                    with open(path, "a", encoding="utf-8") as fs:
                        fs.write("\n" + data)
                except Exception as err:
                    st.error(f"An error occurred: {err}")
                else:
                    st.success("Appended successfully.")

        else:  # Overwrite
            try:
                current = path.read_text(encoding="utf-8")
            except Exception as err:
                st.error(f"Couldn't open this file: {err}")
            else:
                with st.form("overwrite_form"):
                    data = st.text_area("What do you want to write?", value=current, height=250)
                    go = st.form_submit_button("Overwrite")
                if go:
                    try:
                        path.write_text(data, encoding="utf-8")
                    except Exception as err:
                        st.error(f"An error occurred: {err}")
                    else:
                        flash("success", f"'{selected}' overwritten successfully.")
                        st.rerun()

# ---------- DELETE ----------
with tab_delete:
    if not files:
        st.info("No files to delete.")
    else:
        selected = st.selectbox("Choose a file to delete", files, key="delete_select")
        confirm = st.checkbox(f"Yes, permanently delete '{selected}'", key=f"confirm_{selected}")
        if st.button("Delete file", type="primary", disabled=not confirm):
            try:
                (BASE_DIR / selected).unlink()
            except Exception as err:
                st.error(f"An unexpected error occurred: {err}")
            else:
                flash("success", f"'{selected}' deleted successfully.")
                st.rerun()
