import streamlit as st
import pandas as pd
import plotly
import plotly.express as px

# Вивід версій Streamlit та Plotly
st.sidebar.write(f"Версія Streamlit: {st.__version__}")
st.sidebar.write(f"Версія Plotly: {plotly.__version__}")


# Налаштування сторінки для ширшого виводу
st.set_page_config(layout="wide")

# Налаштування заголовку застосунку
st.title("Часовий ряд з вибором ознак, діапазону дат, періодичності та індикаторів")

# Бокова панель для налаштувань
st.sidebar.header("Налаштування")

# Поле для завантаження CSV файлу
uploaded_file = st.sidebar.file_uploader("Завантажте CSV файл", type=["csv"])

if uploaded_file is not None:
    # Завантаження даних
    df = pd.read_csv(uploaded_file)
    
    # Перевірка наявності стовпця з датою
    date_column = None
    for col in df.columns:
        if pd.to_datetime(df[col], errors='coerce').notna().all():
            date_column = col
            df[date_column] = pd.to_datetime(df[date_column])
            break
    
    if date_column:
        # Вибір ознак, окрім дати
        features = [col for col in df.columns if col != date_column]
        
        # Вибір ознак за допомогою чекбоксів
        selected_features = st.sidebar.multiselect(
            "Виберіть ознаки для відображення",
            options=features,
            default=features
        )
        
        # Поле для вибору діапазону дат
        min_date, max_date = df[date_column].min(), df[date_column].max()
        date_range = st.sidebar.date_input(
            "Виберіть діапазон дат",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Поле для вибору періодичності
        resample_frequency = st.sidebar.selectbox(
            "Виберіть періодичність",
            options=["День", "Тиждень", "Місяць", "Рік"],
            index=0
        )
        
        # Мапування вибраної періодичності на формат для ресемплінгу
        frequency_map = {
            "День": "D",
            "Тиждень": "W",
            "Місяць": "M",
            "Рік": "Y"
        }
        frequency = frequency_map[resample_frequency]
        
        # Вибір індикатора та параметрів
        indicator = st.sidebar.selectbox(
            "Виберіть індикатор",
            options=["Без індикатора", "Проста ковзна середня (SMA)", "Експоненційна ковзна середня (EMA)"]
        )
        
        # Налаштування параметрів для вибраного індикатора
        window_size = None
        if indicator in ["Проста ковзна середня (SMA)", "Експоненційна ковзна середня (EMA)"]:
            window_size = st.sidebar.number_input("Введіть розмір вікна для індикатора", min_value=1, value=5)
        
        # Фільтрація даних за вибраним діапазоном дат
        filtered_df = df[(df[date_column] >= pd.to_datetime(date_range[0])) & 
                         (df[date_column] <= pd.to_datetime(date_range[1]))]
        
        # Ресемплінг даних
        resampled_df = filtered_df.set_index(date_column).resample(frequency).mean().reset_index()
        
        # Обчислення індикатора, якщо він обраний
        if indicator == "Проста ковзна середня (SMA)" and window_size:
            for feature in selected_features:
                resampled_df[f"SMA_{window_size}_{feature}"] = resampled_df[feature].rolling(window=window_size).mean()
            selected_features += [f"SMA_{window_size}_{feature}" for feature in selected_features]
        
        elif indicator == "Експоненційна ковзна середня (EMA)" and window_size:
            for feature in selected_features:
                resampled_df[f"EMA_{window_size}_{feature}"] = resampled_df[feature].ewm(span=window_size, adjust=False).mean()
            selected_features += [f"EMA_{window_size}_{feature}" for feature in selected_features]
        
        # Відображення графіка Plotly з використанням всього простору контейнера
        if selected_features:
            fig = px.line(resampled_df, x=date_column, y=selected_features, title=f"Часовий ряд з індикатором: {indicator}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Будь ласка, виберіть хоча б одну ознаку для відображення.")
    else:
        st.sidebar.write("Не вдалося визначити стовпець з датою. Переконайтеся, що у файлі є відповідний стовпець.")
else:
    st.sidebar.write("Завантажте CSV файл для аналізу.")
