class ShinyModel(object):
    save_list = []
    
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
        values = [getattr(self, key) for key in self.save_list if key != 'id']
        table_name = self.__get_table_name()
        if self.id:
            # update
            settings = [str(self.save_list[i]) + '=' + str(self.values[i]) for i in range(len(self.save_list))]
            cursor.execute("UPDATE ? SET ? WHERE id=?", (table_name, settings, self.id))
        else:
            # insert
            cursor.execute("INSERT INTO ? (?) VALUES (?)", (table_name, ",".join(self.save_list), ','.join(values)))
    
    def delete(self, conn):
        if self.id:
            cursor = conn.cursor()
            table_name = self.__get_table_name()
            cursor.execute('DELETE FROM ? WHERE id=?', (table_name, self.id))
    
