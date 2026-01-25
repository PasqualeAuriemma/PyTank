from machine import RTC
try:
    from display import CENTER, RIGHT
except ImportError:
    CENTER = 1
    RIGHT = 2

class MenuItem:

    def __init__(self, name: str, parent=None, display=None, visible=None):
        self._parent = parent
        self.name = name
        self._visible = True if visible is None else visible
        self._display = display
        
    @property
    def visible(self):
        return self._visible

    @property
    def display(self):
        return self._display

    @display.setter
    def display(self, value):
        self._display = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
    
    def draw(self):
        # called when someone click on menu item
        raise NotImplementedError()

    def click(self):
        raise NotImplementedError()

class MenuView(MenuItem):
    def __init__(self, display, name: str, parent=None, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, visible=None):
        super().__init__(name, parent, display, visible)
        self.per_page = per_page
        self.line_height = line_height
        self.font_width = font_width
        self.font_height = font_height
        
    def _menu_header(self, text):
        pass

    def up(self):
        # called when menu.move(-1) is called
        pass

    def down(self):
        # called when menu.move(1) is called
        pass

    def right(self):
        # called when menu.move(1) is called
        pass

    def left(self):
        # called when menu.move(1) is called
        pass
    
    def select(self):
        #print("Sono qua select")
        # called when menu.click() is called (on button press)
        # should return Instance of MenuItem (usually self.parent - if want to go level up or self to stay in current context)
        raise NotImplementedError()
    
    def reset(self):
        raise NotImplementedError()  

class MenuCallback(MenuItem):

    def __init__(self, name: str, callback=None, decorator=None, visible=None, parent=None, display=None):
        super().__init__(name, parent, display, visible)
        self._callback = callback
        self._decorator = '' if decorator is None else decorator
        self._is_active = False
        
    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @property
    def decorator(self):
        return self._decorator if not callable(self._decorator) else self.decorator()

    @decorator.setter
    def decorator(self, value):
        self._decorator = value

    @property
    def visible(self):
        return self._visible if not self._check_callable(self._visible, False) else self._call_callable(self._visible)

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, callback):
        self._check_callable(callback)
        self._callback = callback

    @staticmethod
    def _check_callable(param, raise_error=True):
        if not (callable(param) or (type(param) is tuple and callable(param[0]))):
            if raise_error:
                raise ValueError('callable param should be callable or tuple with callable on first place!')
            else:
                return False
        return True

    @staticmethod
    def _call_callable(func, *args):
        if callable(func):
            return func(*args)
        elif type(func) is tuple and callable(func[0]):
            in_args = func[1] if type(func[1]) is tuple else (func[1],)
            return func[0](*tuple(list(in_args) + list(args)))

class MenuRow(MenuCallback):
    def __init__(self, name, callback=None, decorator=None, visible=None, parent=None, display=None):
        super().__init__(name, callback, decorator, visible, parent, display)
        
    def upd_decorator(self):
        pass

    def draw(self, pos, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8):
        self.upd_decorator()
        menu_y_end = int((self.display.height - line_height) / per_page)
        y = menu_y_end + (pos * menu_y_end)
        v_padding = int((menu_y_end - font_height) / 2)
        background = int(self.is_active)
        self.display.fill_rect(0, y, self.display.width, menu_y_end, background)
        self.display.text(self.name, 0, y + v_padding, int(not background))
        x_pos = self.display.width - (len(self.decorator) * font_width) - 1
        self.display.text(self.decorator, x_pos, y + v_padding, int(not background))

class MenuList(MenuView):

    def __init__(self, display, name: str, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, parent, per_page, line_height, font_width, font_height, visible)
        self._items = []
        self._visible_items = []
        self.selected = 0
        
    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, values):
        self._items = values        
    
    def add(self, item, parent=None):
        item.parent = self if parent is None else parent
        item.display = self.display
        row = ListItem(item, self.visible)
        self._items.append(row)
        return self

    def reset(self):
        self.selected = 0

    def __get_visible_item(self):
        self._visible_items = []
        for item in self._items:
            if item.visible:
                self._visible_items.append(item)
        return self._visible_items
    
    def count(self) -> int:
        elements = len(self.__get_visible_item())    
        return elements

    def up(self) -> None:
        self.selected = self.selected - 1
        if self.selected < 0:
            self.selected = self.count() - 1

    def down(self) -> None:
        self.selected = self.selected + 1
        if self.selected > self.count() - 1:
            self.selected = 0

    def get(self, position):
        if position < 0 or position > self.count():
            return None
        else:
            item = self._visible_items[position]
            if hasattr(self, 'selected_item'):
                item.decorator = '<<' if position == self.selected_item else ''
            item.is_active = position == self.selected
            return item

    def click(self):
        self.draw()
        return self

    def select(self) -> None:
        item = self.get(self.selected)
        return item

    def draw(self):     
        self.display.fill(0)
        self._menu_header(self.name)
        elements = self.count()
        start = self.selected - self.per_page + 1 if self.selected + 1 > self.per_page else 0
        end = start + self.per_page
        menu_pos = 0
        for i in range(start, end if end < elements else elements):
            self.get(i).draw(menu_pos, per_page = self.per_page, line_height = self.line_height)
            menu_pos += 1
        
        self.display.show()

    def _menu_header(self, text):
        x = int((self.display.width / 2) - (len(text) * self.font_width / 2))
        self.display.text(str.upper(self.name), x, 0, 1)
        self.display.hline(0, self.line_height, self.display.width, 1)

class ToggleItem(MenuCallback):
    def __init__(self, dispaly, name, state_callback, change_callback, toggleValue = ('[x]', '[ ]'), parent = None, visible=None, display=None):
        super().__init__(name, change_callback, '', visible, parent, display)
        self._check_callable(state_callback)
        self.state_callback = state_callback
        self.toggleValue = toggleValue
        #print("ToggleItem init name " + self.name + " and it is visible " + str(self.visible) + " and it is visible 2 " + str(visible))
        self.upd_decorator()

    def check_status(self):
        return self._call_callable(self.state_callback)
    
    def upd_decorator(self):
        self.decorator = self.toggleValue[0] if self.check_status() else self.toggleValue[1] 
        #print("ToggleItem decorator setting " + self.decorator)

    def click(self):
        #print("Toggle item click " + self.name + " parent " + str(self.parent) +  " visible " + str(self.visible))
        self._call_callable(self.callback)
        self.upd_decorator()
        #print("Toggle item click parent name " + self.parent.name)
        self.parent.draw()
        return self.parent

class BackItem(MenuCallback):

    def __init__(self, dispaly, name ='<<< BACK', parent = None, exit = False):
        super().__init__(name)

    def click(self):
        self.parent.reset()
        self.parent.parent.draw()
        return self.parent.parent
    
class ListItem(MenuRow):

    def __init__(self, obj, visible=None):
        self.obj = obj
        self.obj_decorator = self.get_after_check_decorator()
        self.visible_value = self.obj.visible if visible is None else visible
        super().__init__(obj.name, decorator=self.obj_decorator, visible=visible, parent=obj.parent, display=obj.display)
        
    @property
    def visible(self):
        if hasattr(self.obj, 'visible'):
            if not isinstance(self.obj.visible, bool):
                return True if not self._check_callable(self.obj.visible, False) else self._call_callable(self.obj.visible)
            else:    
                return self.obj.visible  
        else:
            return True

    
    def get_after_check_decorator(self):
        return self.obj.decorator if hasattr(self.obj, 'decorator') else '>'

    def upd_decorator(self):
        self.decorator = self.obj.decorator if hasattr(self.obj, 'decorator') else '>' 
        
    def click(self):
        return self.obj.click()

class EnumItem(MenuRow):

    def __init__(self, name, callback = None, parent = None, decorator = '', visible=None, display=None):
        super().__init__(name, callback, decorator, visible, parent, display)
        
    def click(self):
        self._call_callable(self.callback)
        self.parent.selected_item = self.callback[1]
        self.parent.decorator = self.parent.get(self.callback[1]).name
        self.parent.reset()
        self.parent.parent.draw()
        return self.parent.parent

class ConfirmItem(MenuRow):

    def __init__(self, name, callback = None, parent = None, decorator = '', visible=None, display=None):
        super().__init__(name, callback, decorator, visible, parent, display)
        
    def click(self):
        if self.callback[-1] == 0:
            self._call_callable((self.callback[0], True))           
        else:
            self._call_callable((self.callback[0], False))   
        self.parent.reset()
        self.parent.parent.draw()
        return self.parent.parent

class ButtonItem(MenuRow):

    def __init__(self, name, callback = None, parent = None, decorator = '', visible=None, display=None):
        super().__init__(name, callback, decorator, visible, parent, display)
        print(name)
        
    def click(self):
        self._call_callable(self.callback)
        self.parent.draw()
        return self.parent

class MenuEnum(MenuList):

    def __init__(self, display, name: str, items, callback, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, per_page, line_height, font_width, font_height, parent, visible)
        self.selected_item = 0 
        if not isinstance(items, list):
            raise ValueError("items should be a list!")
        self.callback = callback
        self.add_items(items, self) 
        self.decorator = self.get(self.selected_item).name

    @property
    def decorator(self):
        return self._decorator if not callable(self._decorator) else self.decorator()

    @decorator.setter
    def decorator(self, value):
        self._decorator = value     
         
    def add(self, item, parent=None):
        self._items.append(item)
    
    def add_items(self, items: list, parent=None):
        for pos, item in enumerate(items):
            row = EnumItem(str(item), (self.callback, pos), parent, display=self.display)
            self.add(row)

class MenuConfirm(MenuList):

    def __init__(self, display, name: str, items, callback, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, per_page, line_height, font_width, font_height, parent, visible)
        if not isinstance(items, tuple):
            raise ValueError("items should be a tuple!")
        self.callback = callback
        self.add_items(items, self) 
              
    def add(self, item, parent=None):
        self._items.append(item)
    
    def add_items(self, items: list, parent=None):
        for pos, item in enumerate(items):
            row = ConfirmItem(str(item), (self.callback, pos), parent, display=self.display,)
            self.add(row)

class MenuMonitoringSensor(MenuView):

    def __init__(self, display, name, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, parent, per_page, line_height, font_width, font_height, visible)
        self.status = False
        self.measure = 0
        self.temperature = 0
        self._switch = False
    
    @property
    def switch(self):
        return self._switch

    @switch.setter
    def switch(self, value):
        self._switch = value

    def updatingValues(self, value, temp):
        self.measure = value
        self.temperature = temp
        if self.switch:
            self.draw()

    def select(self):
        self.switch = not self.switch
        return self.parent

    def draw(self):
        self.display.fill(0)
        self.display.rect(0, 0, self.display.width, self.display.height, 1)
        self._centered_text('WIFI: ' + str(self.measure) , 20, 1)
        self._centered_text('TEMPERATURE: ' + str(self.temperature) , 34, 1)
        self._centered_text('225.10.110.30', 44, 1)
        self.display.show()

    def click(self):  
        self.switch = not self.switch
        self.draw()
        return self
    
    def _centered_text(self, text, y, c):
        x = int(self.display.width/2 - len(text)*8/2)
        self.display.text(text, x, y, c)

class MenuSetDateTime(MenuView):

    def __init__(self, display, name, callback, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, parent, per_page, line_height, font_width, font_height, visible)
        self._gg = 1
        self._mm = 1
        self._mm_max = 12
        self._yy = 2025
        self._hh = 0
        self._m = 0
        self.amount = 0
        self.callback = callback

    @property
    def gg(self):
        return self._gg 
    
    @gg.setter
    def gg(self, _value):
        max_value = self.max_day_month()
        if _value > max_value:
            self._gg = 1
        elif _value < 1:
            self._gg = max_value 
        else:
            self._gg = _value    

    @property
    def mm(self):
        return self._mm 
    
    @mm.setter
    def mm(self, value_mm):
        if value_mm > self._mm_max:
            self._mm = 1
        elif value_mm < 1:
            self._mm = self._mm_max
        else:
            self._mm = value_mm
            if value_mm == 2 and self._gg > self.max_day_month():
                self._gg = self.max_day_month()

    @property
    def m(self):
        return self._m 
    
    @m.setter
    def m(self, value):
        m_max = 60
        if value >= m_max:
            self._m = 0
        elif value < 0:
            self._m = m_max - 1
        else:
            self._m = value

    @property
    def hh(self):
        return self._hh 
    
    @hh.setter
    def hh(self, value):
        hh_max = 24
        if value > hh_max - 1:
            self._hh = 0
        elif value < 0:
            self._hh = hh_max - 1
        else:
            self._hh = value
                        
    @property
    def yy(self):
        return self._yy
    
    @yy.setter
    def yy(self, value):
        self._yy = value

    def max_day_month(self):
        if self.mm == 2:
            if self.yy % 100 == 0:
                # might be leap
                if self.yy % 400 == 0:
                    return 29
                else:
                    return 28
            else:
                # might be leap
                if self.yy % 4 == 0:
                    return 29
                else:
                    return 28
        elif self.mm in (4, 6, 9, 11):
            return 30
        else:
            return 31    

    def draw(self):
        self.display.fill(0)
        background = self.amount == 1
        x_pos1 = int((self.display.width - (10 * 8))/2)
        x_pos2 = x_pos1 + 24
        x_pos3 = x_pos2 + 24
        if self.amount == 0:
            self.display.rect(x_pos1 - 2, 17, (2 * 10), 14, 1)
        elif self.amount == 1:
            self.display.rect(x_pos2 - 2, 17, (2 * 10), 14, 1)
        elif self.amount == 2:
            self.display.rect(x_pos3 - 2, 17, (4 * 9), 14, 1)
        elif self.amount == 3:
            self.display.rect(x_pos1 - 2, 45, (2 * 10), 14, 1)  
        else:
            self.display.rect(x_pos2 - 2, 45, (2 * 10), 14, 1) 
        self.display.text("DATA:", 0, 8, 1)
        self.display.text("{:02d}".format(self.gg), x_pos1, 20, 1)
        self.display.text("{:02d}".format(self.mm), x_pos2, 20, 1)
        self.display.text("{:04d}".format(self.yy), x_pos3, 20, 1)
        self.display.text("ORARIO:", 0, 35, 1)
        self.display.text("{:02d}".format(self.hh), x_pos1, 48, 1)
        self.display.text("{:02d}".format(self.m), x_pos2, 48, 1)    
        self.display.hline(0, 3, self.display.width, 1)
        self.display.show()
    
    def click(self):  
        self.draw()
        return self

    def select(self):
        # Set the time and date
        rtc = RTC()
        rtc.datetime((self._yy, self._mm, self._gg, self._hh, self._m, 0, 0, 0))  # (year, month, day, weekday, hours, minutes, seconds, subseconds)
        return ButtonItem('OK DATATIME', (self.callback, [ self._gg, self._mm, self._yy, self._hh, self._m]), parent=self.parent)

    def up(self):
        if self.amount == 0:
            self.gg = self.gg + 1
        elif self.amount == 1:
            self.mm = self.mm + 1
        elif self.amount == 2:
            self.yy = self.yy + 1
        elif self.amount == 3:
            self.hh = self.hh + 1
        else:
            self.m = self.m + 1

    def down(self):
        if self.amount == 0:
            self.gg = self.gg - 1
        elif self.amount == 1:
            self.mm = self.mm - 1
        elif self.amount == 2:
            self.yy = self.yy - 1
        elif self.amount == 3:
            self.hh = self.hh - 1
        else:
            self.m = self.m - 1

    def right(self):
        self.amount = self.amount + 1
        if self.amount > 4:
            self.amount = 0
        
    def left(self):
        self.amount = self.amount - 1
        if self.amount < 0:
            self.amount = 4

class MenuSetTimer(MenuView):

    def __init__(self, display, name, values, callback, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, parent, per_page, line_height, font_width, font_height, visible)
        self._hh_start = values[0]
        self._min_start = values[1]
        self._hh_end = values[2]
        self._min_end = values[3]
        self._m_max = 60
        self._hh_max = 24
        self.amount = 0
        self.callback = callback

    def _get_value(self, value, max_value):
        if value >= max_value:
            return 0
        elif value < 0:
            return max_value - 1
        else:
            return value

    @property
    def min_start(self):
        return self._min_start 
    
    @min_start.setter
    def min_start(self, value):
        self._min_start = self._get_value(value,self._m_max)
         
    @property
    def hh_start(self):
        return self._hh_start 
    
    @hh_start.setter
    def hh_start(self, value):
        self._hh_start = self._get_value(value, self._hh_max)

    @property
    def min_end(self):
        return self._min_end 
    
    @min_end.setter
    def min_end(self, value):
        self._min_end = self._get_value(value,self._m_max)
         
    @property
    def hh_end(self):
        return self._hh_end 
    
    @hh_end.setter
    def hh_end(self, value):
        self._hh_end = self._get_value(value, self._hh_max)                   

    def draw(self):
        self.display.fill(0)
        background = self.amount == 1
        x_pos1 = int((self.display.width - (7 * 8))/2)
        x_pos2 = x_pos1 + 24
        if self.amount == 0:
            self.display.rect(x_pos1 - 2, 17, (2 * 10), 14, 1)
        elif self.amount == 1:
            self.display.rect(x_pos2 - 2, 17, (2 * 10), 14, 1)
        elif self.amount == 2:
            self.display.rect(x_pos1 - 2, 45, (2 * 10), 14, 1)  
        else:
            self.display.rect(x_pos2 - 2, 45, (2 * 10), 14, 1) 

        self.display.text("ORARIO START:", 0, 8, 1)
        self.display.text("{:02d}".format(self.hh_start), x_pos1, 20, 1)
        self.display.text("{:02d}".format(self.min_start), x_pos2, 20, 1)    
       
        self.display.text("ORARIO END:", 0, 35, 1)
        self.display.text("{:02d}".format(self.hh_end), x_pos1, 48, 1)
        self.display.text("{:02d}".format(self.min_end), x_pos2, 48, 1)    
        self.display.hline(0, 3, self.display.width, 1)
        self.display.show()
    
    def click(self):  
        self.draw()
        return self

    def select(self):
        return ButtonItem('OK TIMER', (self.callback, [self._hh_start,
        self._min_start,
        self._hh_end,
        self._min_end]), parent=self.parent)

    def up(self):
        if self.amount == 0:
            self.hh_start = self.hh_start + 1
        elif self.amount == 1:
            self.min_start = self.min_start + 1
        elif self.amount == 2:
            self.hh_end = self.hh_end + 1
        else:
            self.min_end = self.min_end + 1

    def down(self):
        if self.amount == 0:
            self.hh_start = self.hh_start - 1
        elif self.amount == 1:
            self.min_start = self.min_start - 1
        elif self.amount == 2:
            self.hh_end = self.hh_end - 1
        else:
            self.min_end = self.min_end - 1

    def right(self):
        self.amount = self.amount + 1
        if self.amount > 3:
            self.amount = 0
        
    def left(self):
        self.amount = self.amount - 1
        if self.amount < 0:
            self.amount = 3

class MenuWifiInfo(MenuView):

    def __init__(self, display, name, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, parent, per_page, line_height, font_width, font_height, visible)   
        self.status = False

    def select(self):
        return self.parent

    def click(self):  
        self.draw()
        return self

    def draw(self):
        self.display.fill(0)
        self.display.rect(0, 0, self.display.width, self.display.height, 1)
        self._centered_text('WIFI: '+ str(self.get_status()), 20, 1)
        self._centered_text('225.10.110.30', 34, 1)
        self.display.show()
    
    def get_status(self):
        return self.status

    def activate(self):
        self.status = not self.status
        self.get_status()

    def _centered_text(self, text, y, c):
        x = int(self.display.width/2 - len(text)*8/2)
        self.display.text(text, x, y, c)

class MenuHeaterManage(MenuView):

    def __init__(self, display, name, values,callback, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, parent, per_page, line_height, font_width, font_height, visible)
        self._min_temperature = values[0]
        self._max_temperature = values[1]
        self.amount = 0
        self.callback = callback

    def _get_value(self, value, max_value):
        if value >= max_value:
            return 0
        elif value < 0:
            return max_value - 1
        else:
            return value

    @property
    def min_temperature(self):
        return self._min_temperature 
    
    @min_temperature.setter
    def min_temperature(self, value):
        self._min_temperature = value

    @property
    def max_temperature(self):
        return self._max_temperature 
    
    @max_temperature.setter
    def max_temperature(self, value):
        self._max_temperature = value  
             
    def draw(self):
        self.display.fill(0)
        background = self.amount == 1
        x_pos1 = int((self.display.width - (8))/2)
        if self.amount == 0:
            self.display.rect(x_pos1 - 2, 17, (2 * 10), 14, 1)  
        else:
            self.display.rect(x_pos1 - 2, 45, (2 * 10), 14, 1) 

        self.display.text("MIN TEMPERATURE:", 0, 8, 1)
        self.display.text("{:02d}".format(self.min_temperature), x_pos1, 20, 1)   
       
        self.display.text("MAX TEMPERATURE:", 0, 35, 1)
        self.display.text("{:02d}".format(self.max_temperature), x_pos1, 48, 1)   
        self.display.hline(0, 3, self.display.width, 1)
        self.display.show()
    
    def click(self):  
        self.draw()
        return self

    def select(self):
        if self.min_temperature >= self.max_temperature:
            return MenuError(self.display, self.name, "Error: Max temperature is less than min temperature", parent=self)
        else:    
            return ButtonItem('OK HEATER', (self.callback, [self.min_temperature,
        self.max_temperature]), parent=self.parent)

    def right(self):
        if self.amount == 0:
            self.min_temperature = self.min_temperature + 1
        else:
            self.max_temperature = self.max_temperature + 1

    def left(self):
        if self.amount == 0:
            self.min_temperature = self.min_temperature - 1
        else:
            self.max_temperature = self.max_temperature - 1
        
    def up(self):
        self.amount = self.amount + 1
        if self.amount > 1:
            self.amount = 0
        
    def down(self):
        self.amount = self.amount - 1
        if self.amount < 0:
            self.amount = 1

class MenuError(MenuView):

    def __init__(self, display, name, message, per_page: int = 4, line_height: int = 10, font_width: int = 8, font_height: int = 8, parent = None, visible=None):
        super().__init__(display, name, parent, per_page, line_height, font_width, font_height, visible)   
        self.message = message
        
    def select(self):
        return self.parent

    def click(self):  
        self.draw()
        return self

    def _count_error_row(self, message):
        result = []
        num_char_tot = 0
        temp_row = []
        for word in message.split(" "):
            num_char_word = len(word)
            num_char_word = num_char_word if not temp_row else num_char_word + 1
            num_char_tot = num_char_tot + num_char_word
            if num_char_tot < 16:
                temp_row.append(word)
            else:
                mex=" ".join(temp_row)
                result.append(mex)
                num_char_tot = num_char_word -1
                temp_row = []
                temp_row.append(word)  
        if temp_row:
            result.append(" ".join(temp_row))
        return result

    def draw(self):
        message_rows = self._count_error_row(self.message)
        num_mex = len(message_rows)
        self.display.fill(0)
        self.display.rect(0, 0, self.display.width, self.display.height, 1)
        _center = int(self.display.height/2 - 4)
        _y = _center - (int(num_mex/2)*12)
        for pos, mex in enumerate(message_rows):
            position = _y + (12 * pos)
            self._centered_text(mex, position, 1)

        self.display.show()
    
    def _centered_text(self, text, y, c):
        x = int(self.display.width/2 - len(text)*8/2)
        self.display.text(text, x, y, c)


class Menu:
    current_screen = None

    def __init__(self, parent=None):
        if parent is None:
             raise ValueError("Il parametro 'parent' deve essere presente e non può essere None")
        self.parent = parent
        self.main_screen = None

    def set_main_screen(self, screen: MenuList):
        self.current_screen = screen
        if self.main_screen is None:
            screen.parent = self.parent
            self.main_screen = screen

    def move(self, direction: int = 1):
        self.current_screen.up() if direction < 0 else self.current_screen.down()
        self.draw()

    def shift(self, direction: int = 1):
        self.current_screen.right() if direction < 0 else self.current_screen.left()
        self.draw()

    def click(self):
        self.current_screen = self.current_screen.select()
        if self.current_screen is not None:
            self.current_screen=self.current_screen.click()
            
    def reset(self):
        self.current_screen = self.main_screen
        self.current_screen.selected = 0


    def draw(self):
        return self.current_screen.draw()