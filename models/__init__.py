SAVE_MODELS = ['models.user.User']

class ShinyModel(object):
    
    def __setattr__(self, key, val):
        if hasattr(self, 'save_attr') and key in self.__dict__['save_attr']:
            self.__dict__['save_attr'][key][0] = val
        else:
            self.__dict__[key] = val
    
    def __getattr__(self, key):
        return self.__dict__['save_attr'][key][0]
    
    def __get_table_name(self):
        return getattr(self, 'table_name', self.__class__.__name__.lower())
    
    def load(self, conn, uid):
        cursor = conn.cursor()
        table_name = self.__get_table_name()
        cols = ", ".join(self.save_list)
        cursor.execute('select ? from ? where ?=?', (cols, table_name, 'id', uid))
        row = cursor.fetchone()
        if row and len(row) == len(self.save_list):
            for i in range(len(row)):
                setattr(self, self.save_list[i][0], self.save_list[i][1](row[i]))
    
    def save(self, conn):
        values = []
        cursor = conn.cursor()
        # values = [getattr(self, key) for key in self.save_list if key != 'id']
        table_name = self.__get_table_name()
        if self.id:
            # update
            settings = [key + '=' + val for key,val in self.save_attr.items() if key != self.id]
            cursor.execute("UPDATE ? SET ? WHERE id=?", (table_name, settings, self.id))
        else:
            # insert
            cursor.execute("INSERT INTO ? (?) VALUES (?)", (table_name, ",".join(self.save_list), ','.join(values)))
    
    def delete(self, conn):
        if self.id:
            cursor = conn.cursor()
            table_name = self.__get_table_name()
            cursor.execute('DELETE FROM ? WHERE id=?', (table_name, self.id))
    
