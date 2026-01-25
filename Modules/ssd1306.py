# MicroPython SSD1306 OLED driver, I2C and SPI interfaces
 
from micropython import const
import time
import framebuf

# register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xa4)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_MEM_ADDR        = const(0x20)
SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa0)
SET_MUX_RATIO       = const(0xa8)
SET_COM_OUT_DIR     = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)


# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self._char_dimension = 8
        self.pages = self.height // self.char_dimension
        # Add an extra byte to the data buffer to hold an I2C data/command byte
        # to use hardware-compatible I2C transactions.  A memoryview of the
        # buffer is used to mask this byte from the framebuffer operations
        # (without a major memory hit as memoryview doesn't copy to a separate
        # buffer).
        self.buffer = bytearray((self.pages * self.width) + 1)
        self.buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
        super().__init__(memoryview(self.buffer)[1:], self.width, self.height, framebuf.MONO_VLSB)
        # Provide methods for accessing FrameBuffer graphics primitives. This is a
        # workround because inheritance from a native class is currently unsupported.
        # http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
        self.fill = super().fill
        self.pixel = super().pixel
        self.hline = super().hline
        self.vline = super().vline
        self.line = super().line
        self.rect = super().rect
        self.fill_rect = super().fill_rect
        self.text = super().text
        self.scroll = super().scroll
        self.blit = super().blit
        self.poweron()
        self.init_display()

    @property
    def char_dimension(self):
        return self._char_dimension   

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # address setting
            SET_MEM_ADDR, 0x00,  # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.width > 2 * self.height else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL, 0x30,  # 0.83*Vcc
            # display
            SET_CONTRAST, 0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORM_INV,  # not inverted
            # charge pump
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,):  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()
 
    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)
 
    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)
 
    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)
 
    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))
    
    def show_image(self, img, w, h):
        """
        - image array byte in hex 
        """
        buf_temp = framebuf.FrameBuffer(img, w, h, framebuf.MONO_HLSB)
        self.blit(buf_temp, 0, 0)
        self.show()  

    def show_custom_char(self, img, x, y):
        fb = framebuf.FrameBuffer(img, 8, 8, framebuf.MONO_HLSB)
        self.blit(fb, x, y)
        #self.show()
    
    def show_fill_button_with_text(self, _text, _x, _y, _w , _h):
        # draw a rectangle outline 0,54 to width=19, height=15, colour=1
        self.fill_rect(_x, _y, _w , _h, 1)
        text_size = len(_text) * 8
        x_pixel = _x +(int((_w - text_size)/2) if _w > text_size else 0)
        y_pixel = _y +(int((_h - 8)/2) if _h > 0 else 0)
        self.text(_text, x_pixel , y_pixel, 0)

    def show_blank_button_with_text(self, _text, _x, _y, _w , _h):
        # draw a rectangle outline 0,54 to width=19, height=15, colour=1
        self.rect(_x, _y, _w , _h, 1)
        text_size = len(_text) * 8
        x_pixel = _x +(int((_w - text_size)/2) if _w > text_size else 0)
        y_pixel = _y +(int((_h - 8)/2) if _h > 0 else 0)
        self.text(_text, x_pixel , y_pixel, 1)    

    def write_text(self, _text, x, y, size):
        ''' Method to write Text on OLED/LCD Displays with a variable font size

            Args:
                text: the string of chars to be displayed
                x: x co-ordinate of starting position
                y: y co-ordinate of starting position
                size: font size of text
                color: color of text to be displayed
        '''
        background = 0
        # clear screen
        self.fill(background)
        info = []
        # Creating reference characters to read their values
        self.text(_text, x, y)
        for i in range(x, x + (8 * len(_text))):
            for j in range(y, y + 8):
                # Fetching and saving details of pixels, such as
                # x co-ordinate, y co-ordinate, and color of the pixel
                px_color = self.pixel(i, j)                
                info.append((i, j, px_color))
        # Clearing the reference characters from the screen
        self.text(_text, x, y, background)        
        # Writing the custom-sized font characters on screen
        for px_info in info:
            self.fill_rect(size * px_info[0] - (size - 1) * x,
                           size * px_info[1] - (size - 1) * y,
                           size, size, px_info[2])

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_framebuf()

    def scroll_portion(self, screen, _w, _h):
        self.text(screen[0][2], screen[0][0], screen[0][1])
        self.show()        
        # Scroll a portion of the screen
        for i in range(_h):
            self.fill(0)
            self.text(screen[0][2], screen[0][0], screen[0][1] + i)
            self.show()
            time.sleep(0.05)

        self.text(screen[1][2], screen[1][0], screen[1][1])
        self.show()
         
        for j in range(_h):
            self.fill(0)
            self.text(screen[0][2], screen[0][0], _h)
            self.text(screen[1][2], screen[1][0], screen[1][1] - j)
            self.show()
            time.sleep(0.05)
    
    def clear_portion(self, x, y, w, h):
        '''
            Clear the same portion
        '''    
        for i in range(x, x + w):    
            for j in range(y, y + h):
                self.pixel(i, j, 0)
                self.show()
 
    def head(self, _text):
        text_size = len(_text)
        _x = (((self.width/8)/2) - (text_size/2)) * 8
        self.text(_text, int(_x), 0)
        self.hline(0, 10, 128, 1) 
        #self.show() 

    def foo(self, arrow_position):
        self.hline(0, 54, 128, 1)
        if arrow_position == 'left':
            self.show_fill_button_with_text("<=", 0, 54, 25 , 13)
        elif arrow_position == 'right':
            self.show_fill_button_with_text("=>", 110, 54, 25 , 13)
        elif arrow_position == 'ok':
            self.show_fill_button_with_text("OK", 55, 54, 20 , 13)
        elif arrow_position == 'leftok':
            self.show_fill_button_with_text("<=", 0, 54, 25 , 13)
            self.show_fill_button_with_text("OK", 55, 54, 20 , 13)
        else:
            self.show_fill_button_with_text("<=", 0, 54, 25 , 13)
            self.show_fill_button_with_text("=>", 105, 54, 25 , 13)
        #self.oled.show()

    def scroll_out_screen(self, speed):
        """
        Scroll out horizontally
        It accepts as argument a number that controls the scrolling speed.
        The speed must be a divisor of 128 (oled_width).
        - speed is a number
        """
        for i in range ((self.width+1)/speed):
            for j in range (self.height):
                self.pixel(i, j, 0)
            self.scroll(speed,0)
            self.show()

    def scroll_screen_in_out(self, screen):
        """
        Continuous horizontal scroll
        If you want to scroll the screen in and out continuously,
        you can use the scroll_screen_in_out(screen) function instead.
        
        - screen = [[0, 0 , screen1_row1], [0, 16, screen1_row2], [0, 32, screen1_row3]]
        Each list of the list contains the x coordinate,
        the y coordinate and the message [x, y, message].

        As an example, we will display three rows on the first screen with the following messages.
        screen1_row1 = "Screen 1, row 1"
        screen1_row2 = "Screen 1, row 2"
        screen1_row3 = "Screen 1, row 3"

        """
        for i in range (0, (self.width+1)*2, 1):
            for line in screen:
                self.text(line[2], -self.width+i, line[1])
            self.show()
            if i!= self.width:
                self.fill(0)  

    def scroll_in_screen_v(self, screen):
        """
        Scroll in vertically
        The scroll_in_screen_v(screen) scrolls in the content of the entire screen.
        - screen is a list of [x, y, message]
        """
        for i in range (0, (self.height+1), 1):
            for line in screen:
                self.text(line[2], line[0], -self.height+i+line[1])
            self.show()
            if i!= self.height:
                self.fill(0)           

    def scroll_out_screen_v(self, speed):
        """
        Scroll out vertically
        You can use the scroll_out_screen_v(speed) function to scroll out the screen vertically. 
        Similarly to the horizontal function, it accepts as argument, 
        the scrolling speed that must be a number divisor of 64 (oled_height).
        - speed is a number 
        """
        for i in range ((self.height+1)/speed):
            for j in range (self.width):
                self.pixel(j, i, 0)
            self.scroll(0,speed)
            self.show()  

    def scroll_screen_in_out_v(self, screen):
        """
        Continuous vertical scroll
        If you want to scroll the screen in and out vertically continuously,
        you can use the scroll_in_out_screen_v(screen) function.
        - screen is a list of [x, y, message]
        """
        for i in range (0, (self.height*2+1), 1):
            for line in screen:
                self.text(line[2], line[0], -self.height+i+line[1])
            self.show()
            if i!= self.height:
                self.fill(0)   

     

class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3c, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)
 
    def write_cmd(self, cmd):
        self.temp[0] = 0x80 # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_framebuf(self):
        # Blast out the frame buffer using a single I2C transaction to support
        # hardware I2C interfaces.
        self.i2c.writeto(self.addr, self.buffer)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)    

    def poweron(self):
        pass    

class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        self.rate = 10 * 1024 * 1024
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        self.buffer = bytearray((height // 8) * width)
        self.framebuf = framebuf.FrameBuffer1(self.buffer, width, height)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs.high()
        self.dc.low()
        self.cs.low()
        self.spi.write(bytearray([cmd]))
        self.cs.high()

    def write_framebuf(self):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs.high()
        self.dc.high()
        self.cs.low()
        self.spi.write(self.buffer)
        self.cs.high()

    def poweron(self):
        self.res.high()
        time.sleep_ms(1)
        self.res.low()
        time.sleep_ms(10)
        self.res.high()