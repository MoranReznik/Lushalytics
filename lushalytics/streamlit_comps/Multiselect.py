import streamlit as st

def chips_multiselect(opts, label="Label", key="chips_multiselect"):
    sk = f"{key}_sel"
    opts_map = {str(o): o for o in opts}

    if sk not in st.session_state:
        st.session_state[sk] = set(str(o) for o in opts)
        for s in opts_map:
            st.session_state[f"{key}_{s}"] = True

    col = st.get_option("theme.primaryColor") or "#F63366"
    css = f"""
    <style>
    .chip-bar {{
    display: flex;
    align-items: center;
    height: 2.5rem;
    overflow-x: auto;
    scrollbar-width: none; /* Firefox */
    -ms-overflow-style: none; /* IE 10+ */
    white-space: nowrap;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 0 5px 0 5px;
    margin: 0;
    background: #fff;
    flex: 1;
    }}
    .chip-bar::-webkit-scrollbar {{
    display: none; /* Chrome, Safari and Opera */
    }}
    .chip {{
    display: inline-block;
    background: {col};
    color: #fff;
    border: 1px solid {col};
    border-radius: 4px;
    padding: 0 10px;
    margin: 0 4px 0 0;
    font-size: 12px;
    line-height: 24px;
    }}
    </style>
    """
    st.html(css)

    with st.container():
        with st.container(border=True):
            c_btn, c_bar = st.columns([4, 6], gap="small")

            with c_btn:
                with st.popover(label, use_container_width=True):
                    q = st.text_input("Search", key=f"{key}_search")
                    flt = [s for s in opts_map if q.lower() in s.lower()]

                    if st.button("All", key=f"{key}_all", use_container_width=True):
                        for s in flt:
                            st.session_state[f"{key}_{s}"] = True
                    if st.button("Clear", key=f"{key}_clr", use_container_width=True):
                        for s in opts_map:
                            st.session_state[f"{key}_{s}"] = False

                    for s in flt:
                        st.checkbox(s, key=f"{key}_{s}")

                    st.session_state[sk] = {s for s in opts_map
                                            if st.session_state.get(f"{key}_{s}", False)}

            with c_bar:
                chips = "".join(f'<span class="chip">{s}</span>'
                                for s in st.session_state[sk])
                st.html(f'<div class="chip-bar">{chips}</div>')

    return [opts_map[s] for s in st.session_state[sk]]

def popup_multiselect(opts, label="Label", key="chips_multiselect"):
    sk = f"{key}_sel"
    opts_map = {str(o): o for o in opts}

    if sk not in st.session_state:
        st.session_state[sk] = set(opts_map)
        for s in opts_map:
            st.session_state[f"{key}_{s}"] = True

    with st.popover(label, use_container_width=True):
        st.markdown(
            '<style>div.stButton>button{width:100%;text-align:center}</style>',
            unsafe_allow_html=True,
        )
        if st.button("All", key=f"{key}_all", use_container_width=True):
            for s in opts_map:
                st.session_state[f"{key}_{s}"] = True
        if st.button("Clear", key=f"{key}_clr", use_container_width=True):
            for s in opts_map:
                st.session_state[f"{key}_{s}"] = False

        for s in opts_map:
            st.checkbox(s, key=f"{key}_{s}")

        st.session_state[sk] = {
            s for s in opts_map if st.session_state.get(f"{key}_{s}", False)
        }

    return [opts_map[s] for s in st.session_state[sk]]