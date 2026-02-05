(function () {
    // Инициализация всех форм поиска на странице

    this.form = document.querySelectorAll('.search-form')[0];

    // Вынесено в отдельный файл `search/js/range.js`.
    // Оставляем текущую реализацию как fallback на случай, если range.js не подгрузился.
    if (typeof window.initSearchRangeSliders === 'function') {
        window.initSearchRangeSliders(this.form);
        return;
    }

    console.log('Initializing noUiSliders...');
    
    const sliders = this.form.querySelectorAll('.slider');
    console.log('Found sliders:', sliders.length);
    
    if (sliders.length === 0) {
        console.warn('⚠️ Не найдено элементов .slider');
        return;
    }
    
    // Функция для проверки валидности ввода
    const isValidInput = (value, minLimit, maxLimit, isMin, otherValue = null) => {
        if (value === '' || value === null || value === undefined) return false;
        
        const num = parseInt(value);
        if (isNaN(num)) return false;
        
        // Проверка на диапазон
        if (num < minLimit || num > maxLimit) return false;
        
        // Для минимального значения - проверяем, что не больше максимального
        if (isMin && otherValue !== null && num > otherValue) return false;
        
        // Для максимального значения - проверяем, что не меньше минимального
        if (!isMin && otherValue !== null && num < otherValue) return false;
        
        return true;
    };
    
    sliders.forEach((sliderElement, index) => {
        console.log(`Initializing slider ${index + 1}:`, sliderElement);
        
        try {
            // Получаем данные из родительского контейнера
            const container = sliderElement.closest('.range-slider-wrapper');
            if (!container) {
                console.error('Container not found for slider', sliderElement);
                return;
            }
            
            const minLimit = parseInt(container.dataset.min) || 0;
            const maxLimit = parseInt(container.dataset.max) || 100;
            const stepValue = parseInt(container.dataset.step) || 1;
            
            console.log(`Slider ${index + 1} config:`, { minLimit, maxLimit, stepValue });
            
            // Создаем слайдер
            noUiSlider.create(sliderElement, {
                start: [minLimit, maxLimit],
                connect: true,
                step: stepValue,
                range: {
                    'min': minLimit,
                    'max': maxLimit
                },
                pips: null,
            });
            
            console.log(`✅ Slider ${index + 1} created successfully`);
            
            // Находим связанные элементы
            const minDisplay = container.querySelector('.slider-value-min');
            const maxDisplay = container.querySelector('.slider-value-max');
            const minInput = container.querySelector('.slider-min-input');
            const maxInput = container.querySelector('.slider-max-input');
            const minHidden = container.querySelector('.slider-hidden-min');
            const maxHidden = container.querySelector('.slider-hidden-max');
            
            // Получаем экземпляр слайдера
            const slider = sliderElement.noUiSlider;
            
            // Обновляем отображение при изменении слайдера
            slider.on('update', function(values, handle) {
                const minVal = Math.round(values[0]);
                const maxVal = Math.round(values[1]);
                
                console.log(`Slider ${index + 1} updated:`, minVal, maxVal, 'handle:', handle);
                
                // Обновляем отображение
                if (minDisplay) minDisplay.textContent = minVal;
                if (maxDisplay) maxDisplay.textContent = maxVal;
                
                // Обновляем скрытые поля
                if (minHidden) minHidden.value = minVal;
                if (maxHidden) maxHidden.value = maxVal;
                
                // Обновляем input поля без проверки на активность
                // Проверяем только чтобы не создавать циклическое обновление
                if (handle === 0) {
                    // Двигался левый ползунок - обновляем только минимальное поле
                    if (minInput && minInput.value != minVal) {
                        minInput.value = minVal;
                    }
                } else if (handle === 1) {
                    // Двигался правый ползунок - обновляем только максимальное поле
                    if (maxInput && maxInput.value != maxVal) {
                        maxInput.value = maxVal;
                    }
                } else {
                    // Если handle не указан - обновляем оба поля
                    if (minInput && minInput.value != minVal) {
                        minInput.value = minVal;
                    }
                    if (maxInput && maxInput.value != maxVal) {
                        maxInput.value = maxVal;
                    }
                }
            });
            
            // Функция для восстановления корректного значения
            const restoreValidValue = (input, isMinField, useSliderValue = true) => {
                if (useSliderValue) {
                    const currentValues = slider.get();
                    if (isMinField) {
                        input.value = parseInt(currentValues[0]);
                    } else {
                        input.value = parseInt(currentValues[1]);
                    }
                } else {
                    // Или используем лимиты
                    if (isMinField) {
                        input.value = minLimit;
                    } else {
                        input.value = maxLimit;
                    }
                }
            };
            
            // ОБРАБОТЧИК ДЛЯ INPUT ПОЛЕЙ
            
            // Для минимального значения
            if (minInput) {
                // Добавляем валидацию при вводе
                minInput.addEventListener('keydown', function(e) {
                    // Разрешаем: цифры, backspace, delete, tab, стрелки, точка для чисел с плавающей точкой
                    const allowedKeys = [
                        'Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 
                        'ArrowUp', 'ArrowDown', '.', ','
                    ];
                    
                    // Если это не цифра и не разрешенная клавиша
                    if (!/[0-9]/.test(e.key) && !allowedKeys.includes(e.key)) {
                        e.preventDefault();
                    }
                });
                
                // Валидация при вводе в реальном времени
                minInput.addEventListener('input', function() {
                    const inputValue = this.value;
                    
                    // Если поле пустое, не обновляем слайдер
                    if (inputValue === '') return;
                    
                    const newMin = parseInt(inputValue);
                    if (isNaN(newMin)) {
                        restoreValidValue(this, true);
                        return;
                    }
                    
                    const currentValues = slider.get();
                    const currentMax = parseInt(currentValues[1]);
                    
                    // Проверка валидности ввода
                    if (!isValidInput(newMin, minLimit, maxLimit, true, currentMax)) {
                        // Восстанавливаем предыдущее значение
                        restoreValidValue(this, true);
                    } else {
                        // Обновляем слайдер если значение корректное
                        slider.set([newMin, currentMax]);
                    }
                });
                
                // Валидация при потере фокуса
                minInput.addEventListener('change', function() {
                    const inputValue = this.value;
                    
                    // Если поле пустое, устанавливаем минимальное значение
                    if (inputValue === '') {
                        this.value = minLimit;
                        slider.set([minLimit, slider.get()[1]]);
                        return;
                    }
                    
                    const newMin = parseInt(inputValue);
                    const currentValues = slider.get();
                    const currentMax = parseInt(currentValues[1]);
                    
                    // Проверка валидности
                    if (!isValidInput(newMin, minLimit, maxLimit, true, currentMax)) {
                        // Автоматическая коррекция значения
                        let correctedValue = newMin;
                        
                        // Если меньше минимального лимита
                        if (correctedValue < minLimit) {
                            correctedValue = minLimit;
                        }
                        // Если больше максимального лимита
                        else if (correctedValue > maxLimit) {
                            correctedValue = maxLimit;
                        }
                        // Если больше текущего максимального значения
                        else if (correctedValue > currentMax) {
                            correctedValue = currentMax;
                        }
                        
                        this.value = correctedValue;
                        slider.set([correctedValue, currentMax]);
                    }
                });
                
                // Валидация при попытке вставить текст
                minInput.addEventListener('paste', function(e) {
                    e.preventDefault();
                    
                    // Получаем текст из буфера обмена
                    const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                    const pastedNumber = parseInt(pastedText);
                    
                    if (!isNaN(pastedNumber)) {
                        const currentValues = slider.get();
                        const currentMax = parseInt(currentValues[1]);
                        
                        if (isValidInput(pastedNumber, minLimit, maxLimit, true, currentMax)) {
                            this.value = pastedNumber;
                            slider.set([pastedNumber, currentMax]);
                        }
                    }
                });
            }
            
            // Для максимального значения
            if (maxInput) {
                // Добавляем валидацию при вводе
                maxInput.addEventListener('keydown', function(e) {
                    // Разрешаем: цифры, backspace, delete, tab, стрелки, точка для чисел с плавающей точкой
                    const allowedKeys = [
                        'Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 
                        'ArrowUp', 'ArrowDown', '.', ','
                    ];
                    // Если это не цифра и не разрешенная клавиша
                    if (!/[0-9]/.test(e.key) && !allowedKeys.includes(e.key)) {
                        e.preventDefault();
                    }
                });
                
                maxInput.addEventListener('input', function() {
                    const inputValue = this.value;
                    
                    // Если поле пустое, разрешаем пустое значение
                    if (inputValue === '') return;
                    
                    // Пробуем преобразовать в число
                    const newMax = parseInt(inputValue);
                    if (isNaN(newMax)) {
                        // Если не число, но поле не пустое - возможно пользователь вводит
                        return; // Не восстанавливаем сразу, ждем пока ввод закончится
                    }
                    
                    const currentValues = slider.get();
                    const currentMin = parseInt(currentValues[0]);
                    
                    // Проверка на диапазон, но не проверяем относительно currentMin при вводе
                    // (пользователь может ввести число меньше текущего min, но мы это исправим позже)
                    if (newMax < minLimit) {
                        // Если меньше минимального лимита, не обновляем слайдер
                        return;
                    }
                    
                    if (newMax > maxLimit) {
                        // Если больше максимального лимита, можно либо ограничить, либо не обновлять
                        // Давайте ограничим значением maxLimit
                        this.value = maxLimit;
                        slider.set([currentMin, maxLimit]);
                        return;
                    }
                    
                    // Обновляем слайдер (даже если newMax < currentMin, это исправится в change событии)
                    slider.set([currentMin, newMax]);
                });
                
                maxInput.addEventListener('change', function() {
                    const inputValue = this.value.trim();
                    
                    // Если поле пустое, устанавливаем максимальное значение по умолчанию
                    if (inputValue === '') {
                        this.value = maxLimit;
                        slider.set([slider.get()[0], maxLimit]);
                        return;
                    }
                    
                    const newMax = parseInt(inputValue);
                    const currentValues = slider.get();
                    const currentMin = parseInt(currentValues[0]);
                    
                    // Проверка валидности
                    let finalMax = newMax;
                    
                    if (isNaN(finalMax)) {
                        finalMax = maxLimit;
                    }
                    
                    // Корректируем значение
                    if (finalMax < minLimit) {
                        finalMax = minLimit;
                    }
                    
                    if (finalMax > maxLimit) {
                        finalMax = maxLimit;
                    }
                    
                    if (finalMax < currentMin) {
                        // Если максимальное значение стало меньше минимального,
                        // двигаем и минимальное значение тоже
                        finalMax = Math.max(finalMax, minLimit);
                        slider.set([finalMax, finalMax]); // Устанавливаем оба значения одинаковыми
                        if (minInput) minInput.value = finalMax;
                    } else {
                        slider.set([currentMin, finalMax]);
                    }
                    
                    // Устанавливаем исправленное значение
                    this.value = finalMax;
                });
                
                // Валидация при попытке вставить текст
                maxInput.addEventListener('paste', function(e) {
                    e.preventDefault();
                    
                    // Получаем текст из буфера обмена
                    const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                    const pastedNumber = parseInt(pastedText);
                    
                    if (!isNaN(pastedNumber)) {
                        const currentValues = slider.get();
                        const currentMin = parseInt(currentValues[0]);
                        
                        if (isValidInput(pastedNumber, minLimit, maxLimit, false, currentMin)) {
                            this.value = pastedNumber;
                            slider.set([currentMin, pastedNumber]);
                        }
                    }
                });
            }
            
            // Устанавливаем начальные значения
            if (minDisplay) minDisplay.textContent = minLimit;
            if (maxDisplay) maxDisplay.textContent = maxLimit;
            if (minInput) {
                minInput.value = minLimit;
                minInput.min = minLimit;
                minInput.max = maxLimit;
                minInput.step = stepValue;
                // Добавляем placeholder с подсказкой
                minInput.placeholder = `${minLimit}-${maxLimit}`;
            }
            if (maxInput) {
                maxInput.value = maxLimit;
                maxInput.min = minLimit;
                maxInput.max = maxLimit;
                maxInput.step = stepValue;
                // Добавляем placeholder с подсказкой
                maxInput.placeholder = `${minLimit}-${maxLimit}`;
            }
            if (minHidden) minHidden.value = minLimit;
            if (maxHidden) maxHidden.value = maxLimit;
            
        } catch (error) {
            console.error(`❌ Error creating slider ${index + 1}:`, error);
            this.showError(`Ошибка создания слайдера: ${error.message}`);
        }
    });
})();

