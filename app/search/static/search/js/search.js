// search/static/search/js/search.js
class UniversalSearch {
    constructor(formElement) {
        this.form = formElement;
        this.resultsContainer = document.querySelector(`#results-${this.form.id}`);
        this.resultsList = this.resultsContainer.querySelector('.search-results-list');
        this.loadingElement = this.resultsContainer.querySelector('.search-loading');
        this.configId = this.form.dataset.configId;
        this.contentTypeId = this.form.dataset.contentType;
        this.resultsLimit = this.form.dataset.resultsLimit || 10;
        this.initSelect2();
        this.initNoUISliders();
        this.init();
    }
    
    initSelect2() {
        // Проверяем, что Select2 доступен
        if (typeof $.fn.select2 === 'undefined') {
            console.error('Select2 не загружен!');
            return;
        }
        
        // Инициализация Select2 с настройками для модальных окон
        const select2Options = {
            theme: 'bootstrap-5',
            width: '100%',
            dropdownParent: this.getDropdownParent(), // ВАЖНО для модалок!
            minimumInputLength: 0,
            allowClear: true
        };
        
        // Одиночный выбор
        $(this.form).find('.select2-single').each(function() {
            $(this).select2({
                ...select2Options,
                placeholder: $(this).data('placeholder') || 'Выберите...'
            });
        });
        
        // Множественный выбор
        $(this.form).find('.select2-multiple').each(function() {
            $(this).select2({
                ...select2Options,
                placeholder: $(this).data('placeholder') || 'Выберите варианты...'
            });
        });
        
        // Событие изменения
        $(this.form).on('change', '.select2-single, .select2-multiple', () => {
            if (this.shouldAutoSearch()) {
                this.performSearch();
            }
        });
        
        // Фокус в модальном окне
        this.setupModalFocus();
    }
    
    initNoUISliders() {
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
    }
    
    // Метод для получения данных из No UI Slider
    // getFormData() {
    //     const data = {};
    //     const formData = new FormData(this.form);
        
    //     // Собираем стандартные поля формы
    //     for (let [key, value] of formData.entries()) {
    //         if (value !== '') {
    //             if (key.endsWith('_min') || key.endsWith('_max')) {
    //                 const fieldName = key.replace(/_(min|max)$/, '');
    //                 if (!data[fieldName]) {
    //                     data[fieldName] = {};
    //                 }
    //                 data[fieldName][key.endsWith('_min') ? 'min' : 'max'] = value;
    //             } else {
    //                 data[key] = value;
    //             }
    //         }
    //     }
        
    //     // Дополнительно собираем данные из No UI Slider (на всякий случай)
    //     $(this.form).find('.no-ui-slider-container').each(function() {
    //         alert('?????????????????/')
    //         const $container = $(this);
    //         const fieldName = $container.data('field-name');
    //         const slider = $container.data('slider');
            
    //         if (slider) {
    //             const values = slider.get();
    //             data[fieldName] = {
    //                 min: parseInt(values[0]),
    //                 max: parseInt(values[1])
    //             };
    //         }
    //     });
        
    //     return data;
    // }


    getDropdownParent() {
        // Определяем родительский элемент для dropdown
        // Если форма в модальном окне - используем модальное окно
        const modal = this.form.closest('.modal');
        if (modal) {
            return $(modal);
        }
        
        // Иначе используем body
        return $(document.body);
    }
    
    setupModalFocus() {
        // Обработка фокуса в модальных окнах
        const modal = this.form.closest('.modal');
        if (!modal) return;
        
        // При открытии модалки - фокус на первое поле
        $(modal).on('shown.bs.modal', () => {
            // Даем время на отрисовку Select2
            setTimeout(() => {
                const firstSelect = this.form.querySelector('.select2-selection');
                if (firstSelect) {
                    $(firstSelect).focus();
                } else {
                    const firstInput = this.form.querySelector('input, select, textarea');
                    if (firstInput) {
                        firstInput.focus();
                    }
                }
            }, 100);
        });
        
        // При закрытии модалки - закрываем все dropdowns Select2
        $(modal).on('hide.bs.modal', () => {
            $('.select2-dropdown').remove();
        });
    }
    
    shouldAutoSearch() {
        // Автопоиск только если в основном поле есть текст
        const mainSearch = this.form.querySelector('.search-input');
        return mainSearch && mainSearch.value.length >= 2;
    }
    
    async loadFieldChoices(fieldElement) {
        
        const fieldName = fieldElement.dataset.fieldName;
        const fieldType = fieldElement.dataset.fieldType;
        if (!['select', 'radio'].includes(fieldType)) {
            return;
        }
        
        try {
            const response = await fetch(
                `/search/api/field-choices/${this.configId}/${fieldElement.dataset.fieldId}/`
            );
            
            if (!response.ok) return;
            
            const data = await response.json();
            if (data.success && data.choices.length > 0) {
                this.populateFieldChoices(fieldElement, data.choices, fieldType);
            }
            
        } catch (error) {
            console.error('Error loading choices:', error);
        }
    }
    
    populateFieldChoices(fieldElement, choices, fieldType) {
        if (fieldType === 'select') {
            const select = fieldElement;
            if (select) {
                // Очищаем существующие опции кроме первой
                while (select.options.length > 1) {
                    select.remove(1);
                }
                
                // Добавляем новые опции
                choices.forEach(choice => {
                    const option = document.createElement('option');
                    option.value = choice.value;
                    option.textContent = choice.label;
                    select.appendChild(option);
                });
            }
        } else if (fieldType === 'radio') {
            const container = fieldElement;
            // Очищаем существующие радиокнопки
            container.innerHTML = `<label class="form-label">${fieldElement.dataset.label || 'Выберите'}</label>`;
            
            // Добавляем новые радиокнопки
            choices.forEach((choice, index) => {
                const radioId = `field_${fieldElement.dataset.fieldId}_${index}`;
                const radioHtml = `
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="radio" 
                               name="${fieldElement.dataset.fieldName}"
                               value="${choice.value}"
                               id="${radioId}">
                        <label class="form-check-label" for="${radioId}">
                            ${choice.label}
                        </label>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', radioHtml);
            });
        }
    }

    init() {
        // Событие отправки формы
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        // Событие очистки
        const clearBtn = this.form.querySelector('.search-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearSearch());
        }
        
        // Автопоиск при вводе
        const searchInput = this.form.querySelector('.search-input');
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (e.target.value.length >= 2) {
                        this.performSearch();
                    } else {
                        this.hideResults();
                    }
                }, 500);
            });
        }
        
        // Загружаем динамические choices для полей
        const dynamicFields = this.form.querySelectorAll('[data-field-type="select"], [data-field-type="radio"]');
        dynamicFields.forEach(field => {
            if (field.dataset.fieldId) {
                
                this.loadFieldChoices(field);
            }
        });
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        // Собираем данные формы
        for (let [key, value] of formData.entries()) {
            if (value.trim() !== '') {
                data[key] = value;
            }
        }
        
        // Обрабатываем range поля
        const rangeFields = this.form.querySelectorAll('[data-field-type="range"]');
        rangeFields.forEach(field => {
            const fieldName = field.dataset.fieldName;
            const minInput = this.form.querySelector(`[name="${fieldName}_min"]`);
            const maxInput = this.form.querySelector(`[name="${fieldName}_max"]`);
            
            if (minInput && minInput.value) data[`${fieldName}_min`] = minInput.value;
            if (maxInput && maxInput.value) data[`${fieldName}_max`] = maxInput.value;
        });
        
        return data;
    }
    
    async performSearch() {
        const data = this.getFormData();
        
        // Показываем загрузку
        this.showLoading();
        this.showResults();
        try {
            const response = await fetch('/search/api/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    config_id: this.configId,
                    content_type_id: this.contentTypeId,
                    search_data: data,
                    limit: this.resultsLimit
                })
            });
            
            if (!response.ok) throw new Error('Ошибка поиска');
            
            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('Search error:', error);
            this.displayError('Ошибка при выполнении поиска');
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(result) {
        this.resultsList.innerHTML = '';
        
        if (!result.success) {
            this.displayError(result.message || 'Ошибка поиска');
            return;
        }
        
        if (result.results.length === 0) {
            this.resultsList.innerHTML = `
                <div class="alert alert-info m-2">
                    Ничего не найдено
                </div>
            `;
            return;
        }
        
        // Показываем количество результатов
        if (result.show_count) {
            const countHtml = `
                <div class="search-results-count p-2 border-bottom">
                    <small class="text-muted">Найдено: ${result.total}</small>
                </div>
            `;
            this.resultsList.innerHTML = countHtml;
        }
        
        // Добавляем результаты
        result.results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.dataset.objectId = item.id;
            resultItem.dataset.objectType = item.content_type;
            resultItem.innerHTML = this.formatResultItem(item);
            
            // Событие клика
            resultItem.addEventListener('click', () => {
                this.onResultClick(item);
            });
            
            this.resultsList.appendChild(resultItem);
        });
        
        // Кнопка "Показать все"
        if (result.has_more) {
            const showAllBtn = document.createElement('button');
            showAllBtn.className = 'btn btn-link btn-sm w-100 text-center';
            showAllBtn.textContent = 'Показать все...';
            showAllBtn.addEventListener('click', () => this.showAllResults(result.search_id));
            this.resultsList.appendChild(showAllBtn);
        }
    }
    
    formatResultItem(item) {
        // Кастомизируйте отображение под ваши нужды
        return `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${item.title || `Объект #${item.id}`}</strong>
                    ${item.description ? `<div class="small text-muted">${item.description}</div>` : ''}
                </div>
                <span class="badge bg-secondary">ID: ${item.id}</span>
            </div>
        `;
    }
    
    onResultClick(item) {
        // Событие при клике на результат
        const event = new CustomEvent('search-result-click', {
            detail: {
                id: item.id,
                content_type: item.content_type,
                object: item,
                config_id: this.configId
            },
            bubbles: true
        });
        this.form.dispatchEvent(event);
        
        // По умолчанию - переход на страницу объекта
        if (item.url) {
            window.location.href = item.url;
        }
    }
    
    showAllResults(searchId) {
        // Загрузить все результаты
        console.log('Show all for search:', searchId);
    }
    
    showLoading() {
        this.loadingElement.style.display = 'block';
    }
    
    hideLoading() {
        this.loadingElement.style.display = 'none';
    }
    
    showResults() {
        this.resultsContainer.style.display = 'block';
    }
    
    hideResults() {
        this.resultsContainer.style.display = 'none';
    }
    
    clearSearch() {
        this.form.reset();
        this.hideResults();
        this.resultsList.innerHTML = '';
    }
    
    displayError(message) {
        this.resultsList.innerHTML = `
            <div class="alert alert-danger m-2">
                ${message}
            </div>
        `;
    }
    
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
}

// Инициализация всех форм поиска на странице
document.addEventListener('DOMContentLoaded', function() {
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        new UniversalSearch(form);
    });
});